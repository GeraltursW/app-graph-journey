"""Check the completed film, subtitle bounds, original-rate voices and QA frames."""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
NAME = 'application-knowledge-graph-with-mechanical-replay'


def audio(path, channels=1):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
        '-vn', '-ar', '48000', '-ac', str(channels), '-f', 'f32le', '-'])
    return np.frombuffer(data, dtype='<f4')


def seconds(value):
    h, m, s = value.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    p = parser.parse_args().out.resolve()
    video = p / (NAME + '.mp4')
    timeline = json.loads((p / 'main-integration-timeline.json').read_text('utf-8'))
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-show_streams', '-show_format', '-of', 'json', str(video)]))
    vs = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    als = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
    assert (vs['width'], vs['height'], vs['r_frame_rate']) == (1920, 1080, '60/1')
    assert int(vs['nb_frames']) == round(timeline['duration'] * 60)
    assert abs(float(vs['duration']) - timeline['duration']) < .02
    av_delta = abs(float(vs['duration']) - float(als['duration']))
    assert av_delta < .05
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video),
        '-f', 'null', '-'], capture_output=True)
    assert result.returncode == 0 and not result.stderr, result.stderr

    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 36)
    cues = []
    for line in (p / (NAME + '.zh-CN.ass')).read_text('utf-8').splitlines():
        if not line.startswith('Dialogue:'):
            continue
        values = line.split(',', 9)
        start, end = seconds(values[1]), seconds(values[2])
        text = re.sub(r'\{[^}]*\}', '', values[9])
        assert 0 <= start < end <= timeline['duration']
        assert not cues or start >= cues[-1]['end'] - .01
        width = max(font.getlength(s) for s in text.split(r'\N'))
        assert width < 1740
        cues.append({'start': start, 'end': end, 'width': round(width, 2)})
    assert len(cues) == timeline['caption_count']

    samples = audio(video, channels=2)
    peak = float(np.max(np.abs(samples)))
    assert peak < 1
    stem = audio(p / 'narration.wav')
    manifest = json.loads((ROOT / 'assets/audio/scenario-context/manifest.json').read_text('utf-8'))
    sources = [(s['id'], ROOT / s['audio'], timeline['scenario_start'] + s['start'] + s['voice_offset'])
               for s in manifest['stages']]
    sources.append(('mechanical', ROOT / 'releases/latest/mechanical-natural-voiceover.wav', timeline['mechanical_start']))
    correlations = []
    for name, path, delay in sources:
        source = audio(path)
        start = round(delay * 1000) * 48
        # FFmpeg's sample rounding can differ by one sample at integer milliseconds.
        candidates = [(float(np.corrcoef(source, stem[start + lag:start + lag + len(source)])[0, 1]), lag)
                      for lag in range(-2, 3)]
        corr, lag = max(candidates)
        assert corr > .99999, (name, corr, lag)
        correlations.append({'id': name, 'correlation': corr, 'sample_offset': lag, 'time_stretch': 1.0})

    times = [0, 49.5, 60.59, 61, 61.45, 70, 76, 82, 89.5, 94, 99.8, 105, 114.4, 123, 125.3, 128, 152, 157.5]
    contact = Image.new('RGB', (1600, 1250), (25, 25, 27))
    draw = ImageDraw.Draw(contact)
    for i, time in enumerate(times):
        path = p / f'qa-{time:06.2f}.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(time),
            '-i', str(video), '-frames:v', '1', str(path)], check=True)
        im = Image.open(path)
        im.thumbnail((400, 225))
        x, y = i % 4 * 400, i // 4 * 250
        contact.paste(im, (x, y))
        draw.text((x + 10, y + 230), f'{time:.2f}s', fill='white')
    contact.save(p / 'main-contact.jpg')
    report = {'version': timeline['version'], 'duration': float(vs['duration']),
        'resolution': [1920, 1080], 'fps': 60, 'frames': int(vs['nb_frames']),
        'av_duration_delta': av_delta, 'full_decode_errors': 0,
        'caption_count': len(cues), 'max_caption_width': max(c['width'] for c in cues),
        'caption_checks': 'non-overlap, inside duration and 1740px text width',
        'audio_decoded_stereo_peak': peak,
        'audio_clipped_samples': int(np.count_nonzero(np.abs(samples) >= 1)),
        'voice_checks': correlations,
        'scenario_ui': 'AI-generated illustrative scenario, animated UI rehearsal',
        'visual_review': 'Contact sheet generated; manual review required before publication'}
    (p / 'main-integration-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
