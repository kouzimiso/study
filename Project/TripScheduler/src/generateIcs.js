#!/usr/bin/env node
'use strict';

/**
 * data/*.json（{date, start, end, title, location, description}[]）を
 * iCalendar (.ics) 形式に変換する。日本時間（Asia/Tokyo, UTC+9固定）の
 * 予定として扱い、出力はUTC（Z付き）に変換する。
 *
 * 使い方:
 *   node src/generateIcs.js data/silver-week-2026.json silver-week-2026.ics
 */

const fs = require('fs');
const path = require('path');

function toIcsUtc(date, time) {
  const dt = new Date(`${date}T${time}:00+09:00`);
  if (Number.isNaN(dt.getTime())) {
    throw new Error(`不正な日時: ${date} ${time}`);
  }
  return dt.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
}

function escapeIcsText(str) {
  return String(str || '')
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n');
}

function foldLine(line) {
  // RFC5545: 1行75オクテット超は継続行として折り返す
  const bytes = Buffer.byteLength(line, 'utf8');
  if (bytes <= 75) return line;
  const parts = [];
  let current = line;
  while (Buffer.byteLength(current, 'utf8') > 75) {
    let sliceLen = 75;
    while (Buffer.byteLength(current.slice(0, sliceLen), 'utf8') > 75) sliceLen -= 1;
    parts.push(current.slice(0, sliceLen));
    current = ' ' + current.slice(sliceLen);
  }
  parts.push(current);
  return parts.join('\r\n');
}

/**
 * @param {{date:string,start:string,end:string,title:string,location?:string,description?:string}[]} events
 * @param {{calendarName?: string}} [options]
 * @returns {string} .ics ファイルの中身
 */
function generateIcs(events, options = {}) {
  const now = toIcsUtc(
    new Date().toISOString().slice(0, 10),
    new Date().toISOString().slice(11, 16)
  );

  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//TripScheduler//Silver Week Planner//JA',
    'CALSCALE:GREGORIAN',
    `X-WR-CALNAME:${escapeIcsText(options.calendarName || 'シルバーウィーク旅程')}`,
  ];

  events.forEach((event, index) => {
    const uid = `tripscheduler-${event.date}-${index}@study.local`;
    lines.push(
      'BEGIN:VEVENT',
      `UID:${uid}`,
      `DTSTAMP:${now}`,
      `DTSTART:${toIcsUtc(event.date, event.start)}`,
      `DTEND:${toIcsUtc(event.date, event.end)}`,
      foldLine(`SUMMARY:${escapeIcsText(event.title)}`),
      foldLine(`LOCATION:${escapeIcsText(event.location)}`),
      foldLine(`DESCRIPTION:${escapeIcsText(event.description)}`),
      'END:VEVENT'
    );
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n') + '\r\n';
}

function main() {
  const [, , inputArg, outputArg, calendarNameArg] = process.argv;
  if (!inputArg) {
    console.error('使い方: node src/generateIcs.js <入力JSON> [出力.ics] [カレンダー名]');
    process.exitCode = 1;
    return;
  }
  const inputPath = path.resolve(inputArg);
  const events = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const ics = generateIcs(events, {
    calendarName: calendarNameArg || path.basename(inputPath, '.json'),
  });

  const outputPath = path.resolve(outputArg || inputPath.replace(/\.json$/, '.ics'));
  fs.writeFileSync(outputPath, ics, 'utf8');
  console.log(`生成しました: ${outputPath}`);
}

if (require.main === module) {
  main();
}

module.exports = { generateIcs, toIcsUtc, escapeIcsText };
