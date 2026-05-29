"""PCM audio codec — resampling and μ-law/linear conversion.

Ported from OpenClaw src/talk/audio-codec.ts
"""

from __future__ import annotations

import math
import struct
from array import array

TELEPHONY_SAMPLE_RATE = 8000
RESAMPLE_FILTER_TAPS = 31
RESAMPLE_CUTOFF_GUARD = 0.94
RESAMPLE_MAX_PRECOMPUTED_PHASES = 4096
RESAMPLE_HALF_TAPS = RESAMPLE_FILTER_TAPS // 2

# Precompute window function
_RESAMPLE_WINDOW = tuple(
    0.5 - 0.5 * math.cos(2.0 * math.pi * i / (RESAMPLE_FILTER_TAPS - 1))
    for i in range(RESAMPLE_FILTER_TAPS)
)


def _clamp16(value: float) -> int:
    return max(-32768, min(32767, round(value)))


def _sinc(x: float) -> float:
    if x == 0.0:
        return 1.0
    return math.sin(math.pi * x) / (math.pi * x)


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a or 1


def _read_int16_samples(data: bytes) -> array:
    """Read PCM16 little-endian samples from bytes."""
    n = len(data) // 2
    samples = array("h")
    for i in range(n):
        samples.append(struct.unpack_from("<h", data, i * 2)[0])
    return samples


def _write_int16_samples(samples: array) -> bytes:
    """Write PCM16 little-endian samples to bytes."""
    result = bytearray(len(samples) * 2)
    for i, s in enumerate(samples):
        struct.pack_into("<h", result, i * 2, _clamp16(s))
    return bytes(result)


def _build_resample_kernel(
    input_rate: int, output_rate: int, cutoff: float
) -> tuple[tuple[tuple[float, ...], ...], int, int] | None:
    """Build a precomputed resampling kernel."""
    divisor = _gcd(input_rate, output_rate)
    input_step = input_rate // divisor
    phase_count = output_rate // divisor
    if phase_count > RESAMPLE_MAX_PRECOMPUTED_PHASES:
        return None

    coefficients = []
    for phase_idx in range(phase_count):
        phase = phase_idx / phase_count
        phase_coeffs = []
        for tap in range(-RESAMPLE_HALF_TAPS, RESAMPLE_HALF_TAPS + 1):
            distance = tap - phase
            low_pass = 2.0 * cutoff * _sinc(2.0 * cutoff * distance)
            tap_idx = tap + RESAMPLE_HALF_TAPS
            phase_coeffs.append(low_pass * _RESAMPLE_WINDOW[tap_idx])
        coefficients.append(tuple(phase_coeffs))

    return tuple(coefficients), input_step, phase_count


def resample_pcm(data: bytes, input_rate: int, output_rate: int) -> bytes:
    """Resample PCM16 audio from input_rate to output_rate."""
    if input_rate == output_rate:
        return data

    input_samples = _read_int16_samples(data)
    n_input = len(input_samples)
    if n_input == 0:
        return b""

    ratio = input_rate / output_rate
    n_output = int(n_input / ratio)

    max_cutoff = 0.5
    downsample_cutoff = max_cutoff / ratio if ratio > 1 else max_cutoff
    cutoff = max(0.01, downsample_cutoff * RESAMPLE_CUTOFF_GUARD)

    kernel = _build_resample_kernel(input_rate, output_rate, cutoff)

    output_samples = array("h")
    for i in range(n_output):
        src_pos = i * ratio

        if kernel:
            coeffs, input_step, phase_count = kernel
            center = int(src_pos)
            phase_idx = (i * input_step) % phase_count
            phase_coeffs = coeffs[phase_idx]

            weighted = 0.0
            weight_sum = 0.0
            for tap in range(-RESAMPLE_HALF_TAPS, RESAMPLE_HALF_TAPS + 1):
                sample_idx = center + tap
                if 0 <= sample_idx < n_input:
                    coeff = phase_coeffs[tap + RESAMPLE_HALF_TAPS]
                    weighted += input_samples[sample_idx] * coeff
                    weight_sum += coeff

            if weight_sum == 0:
                nearest = max(0, min(n_input - 1, center))
                sample = input_samples[nearest]
            else:
                sample = weighted / weight_sum
        else:
            center = int(src_pos)
            weighted = 0.0
            weight_sum = 0.0
            for tap in range(-RESAMPLE_HALF_TAPS, RESAMPLE_HALF_TAPS + 1):
                sample_idx = center + tap
                if 0 <= sample_idx < n_input:
                    distance = sample_idx - src_pos
                    low_pass = 2.0 * cutoff * _sinc(2.0 * cutoff * distance)
                    coeff = low_pass * _RESAMPLE_WINDOW[tap + RESAMPLE_HALF_TAPS]
                    weighted += input_samples[sample_idx] * coeff
                    weight_sum += coeff
            if weight_sum == 0:
                nearest = max(0, min(n_input - 1, round(src_pos)))
                sample = input_samples[nearest]
            else:
                sample = weighted / weight_sum

        output_samples.append(_clamp16(sample))

    return _write_int16_samples(output_samples)


def resample_pcm_to_8k(data: bytes, input_rate: int) -> bytes:
    """Resample PCM16 audio to 8kHz (telephony rate)."""
    return resample_pcm(data, input_rate, TELEPHONY_SAMPLE_RATE)


def _linear_to_mulaw(sample: int) -> int:
    BIAS = 132
    CLIP = 32635
    sign = 0x80 if sample < 0 else 0
    if sample < 0:
        sample = -sample
    if sample > CLIP:
        sample = CLIP
    sample += BIAS
    exponent = 7
    exp_mask = 0x4000
    while exponent > 0 and (sample & exp_mask) == 0:
        exponent -= 1
        exp_mask >>= 1
    mantissa = (sample >> (exponent + 3)) & 0x0F
    return (~(sign | (exponent << 4) | mantissa)) & 0xFF


def _mulaw_to_linear(value: int) -> int:
    mu_law = ~value & 0xFF
    sign = mu_law & 0x80
    exponent = (mu_law >> 4) & 0x07
    mantissa = mu_law & 0x0F
    sample = ((mantissa << 3) + 132) << exponent
    sample -= 132
    return -sample if sign else sample


def pcm_to_mulaw(pcm: bytes) -> bytes:
    """Convert PCM16 to μ-law."""
    samples = _read_int16_samples(pcm)
    return bytes(_linear_to_mulaw(s) for s in samples)


def mulaw_to_pcm(mulaw: bytes) -> bytes:
    """Convert μ-law to PCM16."""
    output_samples = array("h", (_clamp16(_mulaw_to_linear(b)) for b in mulaw))
    return _write_int16_samples(output_samples)


def convert_pcm_to_mulaw_8k(pcm: bytes, input_rate: int) -> bytes:
    """Convert PCM16 to μ-law at 8kHz."""
    return pcm_to_mulaw(resample_pcm_to_8k(pcm, input_rate))
