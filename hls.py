"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import re
import sys
import requests
from collections import namedtuple
if sys.version_info > (3,):
  from urllib.parse import urljoin
else:
  from urlparse import urljoin

CSV_PATTERN = re.compile(r'''((?:[^,"' ]|"[^"]*"|'[^']*')+)''')
EXT_INF_DIRECTIVE = "#EXTINF:"
EXT_STREAM_DIRECTIVE = "#EXT-X-STREAM-INF:"
EXT_SEQUENCE_DIRECTIVE = "#EXT-X-MEDIA-SEQUENCE:"

Stream = namedtuple("Stream", "url bandwidth")
Segment = namedtuple("Segment", "url sequence duration")

def is_master(playlist):
  for line in playlist.splitlines():
    if line.startswith(EXT_STREAM_DIRECTIVE):
      return True
    if line.startswith(EXT_INF_DIRECTIVE):
      return False
  return False

def parse_master_playlist(baseurl, playlist):
  playlist = iter(playlist.splitlines())
  streams = []
  for line in playlist:
    if line.startswith(EXT_STREAM_DIRECTIVE):
      line = line.split(EXT_STREAM_DIRECTIVE)[1]
      attributes = CSV_PATTERN.split(line)[1::2]
      info = {}
      for attr in attributes:
        field, value = tuple(attr.split("="))
        info[field] = value
      stream_url = urljoin(baseurl, next(playlist))
      streams.append(Stream(url=stream_url, bandwidth=info['BANDWIDTH']))
  return streams

def parse_stream_playlist(baseurl, playlist):
  playlist = iter(playlist.splitlines())
  sequence = 1
  segments = []
  for line in playlist:
    if line.startswith(EXT_SEQUENCE_DIRECTIVE):
      sequence = int(line.split(EXT_SEQUENCE_DIRECTIVE)[1])
    elif line.startswith(EXT_INF_DIRECTIVE):
      line = line.split(EXT_INF_DIRECTIVE)[1]
      duration = CSV_PATTERN.split(line)[1::2][0]
      segment_url = urljoin(baseurl, next(playlist))
      segments.append(Segment(segment_url, sequence, duration))
      sequence += 1
  return segments

def select_stream(streams, max_bandwidth=float('inf')):
  selected = streams[0]
  for stream in streams[1:]:
    bandwidth = int(stream.bandwidth)
    if int(selected.bandwidth) < bandwidth <= max_bandwidth:
      selected = stream
  return selected

def get_streams(url):
  playlist = requests.get(url).text
  if is_master(playlist):
    return parse_master_playlist(url, playlist)
  return [ Stream(url, '') ]

def get_segments(url, max_bandwidth=float('inf')):
  playlist = requests.get(url).text
  if is_master(playlist):
    stream = select_stream(parse_master_playlist(url, playlist), max_bandwidth)
    url = stream.url
    playlist = requests.get(stream.url).text
  segments = parse_stream_playlist(url, playlist)
  return segments

def download(url, filename, progress_cb=None, abort_cb=None, max_bandwidth=float('inf')):
  aborted = False
  with open(filename, 'wb') as out:
    segments = get_segments(url, max_bandwidth)
    for i, segment in enumerate(segments):
      if abort_cb and abort_cb():
        aborted = True
        break
      r = requests.get(segment.url, stream=True)
      for chunk in r.iter_content(1024):
        out.write(chunk)
      if progress_cb:
        progress_cb(int((i+1)/float(len(segments))*100))
  if aborted:
    os.remove(filename)
