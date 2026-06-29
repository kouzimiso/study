/* =====================================================================
 * gantt_core.js  —  スケジュール/Todo 管理の純粋ロジック（ブラウザ非依存）
 * ---------------------------------------------------------------------
 * Python 版（Sources/Common/ScheduleControl.py, TodoControl.py,
 * Sources/ViewModels/GanttViewModel.py, Sources/Common/PlanRisk.py,
 * Sources/Common/PlanStore.py, Sources/Common/WorkReport.py）の移植。
 *
 * PlanList JSON フォーマット仕様はそのまま。外部プログラム起動は扱わない。
 * このファイルは Node(54件) + jsdom(15件) のテストで検証済み。
 *
 * ブラウザでは window.GanttCore に、Node では module.exports に公開する。
 * ===================================================================== */
(function (root, factory) {
  const mod = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = mod;
  else root.GanttCore = mod;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ===== ScheduleControl 相当: 日時パース / 完了判定 / 発生(occurrence) =====
  const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  function pad2(n) { return String(n).padStart(2, "0"); }

  function parseDt(s, opts) {
    opts = opts || {};
    if (s === null || s === undefined || s === "") return null;
    if (s instanceof Date) return isNaN(s) ? null : s;
    let t = String(s).trim().replace(/T/g, " ").replace(/\s+/g, " ");
    if (!t) return null;
    const sp = t.split(" ");
    let head = sp.shift();
    const tail = sp.join(" ");
    head = head.replace(/[\/.]/g, "-");
    const dm = head.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (dm) {
      const y = +dm[1], mo = +dm[2], d = +dm[3];
      let hh = 0, mm = 0, ss = 0;
      if (tail) {
        const tmm = tail.match(/^(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?$/);
        if (!tmm) return null;
        hh = +tmm[1]; mm = +(tmm[2] || 0); ss = +(tmm[3] || 0);
      } else if (opts.endOfDay) { hh = 23; mm = 59; }
      const dt = new Date(y, mo - 1, d, hh, mm, ss);
      return isNaN(dt) ? null : dt;
    }
    const tm = head.match(/^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/);
    if (tm) {
      const base = opts.baseDate ? new Date(opts.baseDate) : new Date();
      return new Date(base.getFullYear(), base.getMonth(), base.getDate(),
        +tm[1], +tm[2], +(tm[3] || 0));
    }
    return null;
  }
  function formatDt(dt) {
    if (!(dt instanceof Date) || isNaN(dt)) return "";
    return `${dt.getFullYear()}-${pad2(dt.getMonth() + 1)}-${pad2(dt.getDate())} `
      + `${pad2(dt.getHours())}:${pad2(dt.getMinutes())}`;
  }
  function dateStr(d) {
    if (d instanceof Date) return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
    return String(d);
  }
  function dayKeyName(d) { return WEEKDAYS[(d.getDay() + 6) % 7]; }
  function sameDate(a, b) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }
  function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function lastDayOfMonth(y, m) { return new Date(y, m, 0).getDate(); }
  function schedule(plan) { const s = plan.schedule; return (s && typeof s === "object") ? s : {}; }
  function truthy(c) { if (typeof c === "boolean") return c; return c != null && String(c).trim() !== ""; }
  function isKnownNoActionType(t) { return !t || String(t) === "todo"; }
  function isCompleted(plan, occurrenceDate, state) {
    const name = plan.name || "";
    if (occurrenceDate != null) {
      const rec = (state || {})[name] || {};
      const occ = (rec.occurrences || {})[dateStr(occurrenceDate)] || {};
      return truthy(occ.completion);
    }
    if (truthy(schedule(plan).completion)) return true;
    const rec = (state || {})[name] || {};
    return truthy(rec.completion);
  }
  function cronFieldMatch(field, value, lo, hi) {
    for (let part of String(field).split(",")) {
      part = part.trim();
      if (!part) continue;
      let step = 1, rng = part;
      if (part.indexOf("/") >= 0) { const a = part.split("/"); rng = a[0]; step = parseInt(a[1], 10) || 1; }
      let a, b;
      if (rng === "*") { a = lo; b = hi; }
      else if (rng.indexOf("-") >= 0) { const p = rng.split("-"); a = parseInt(p[0], 10); b = parseInt(p[1], 10); if (isNaN(a) || isNaN(b)) continue; }
      else { a = b = parseInt(rng, 10); if (isNaN(a)) continue; }
      if (a <= value && value <= b && (value - a) % Math.max(1, step) === 0) return true;
    }
    return false;
  }
  function cronFirstTime(minF, hourF) {
    for (let h = 0; h < 24; h++) if (cronFieldMatch(hourF, h, 0, 23))
      for (let m = 0; m < 60; m++) if (cronFieldMatch(minF, m, 0, 59)) return [h, m];
    return [0, 0];
  }
  function cronMatchDate(cron, date) {
    const f = String(cron).split(/\s+/).filter(Boolean);
    if (f.length !== 5) return [false, null];
    const [mi, ho, dom, mon, dow] = f;
    if (!cronFieldMatch(mon, date.getMonth() + 1, 1, 12)) return [false, null];
    const cronDow = date.getDay();
    const domR = dom.trim() !== "*", dowR = dow.trim() !== "*";
    const domOk = cronFieldMatch(dom, date.getDate(), 1, 31);
    const dowOk = cronFieldMatch(dow, cronDow, 0, 6);
    let dayOk;
    if (domR && dowR) dayOk = domOk || dowOk;
    else if (domR) dayOk = domOk;
    else if (dowR) dayOk = dowOk;
    else dayOk = true;
    if (!dayOk) return [false, null];
    return [true, cronFirstTime(mi, ho)];
  }
  function occurrenceOn(plan, date) {
    const sch = schedule(plan);
    const start = parseDt(sch.start);
    const end = parseDt(sch.end, { endOfDay: true });
    const rec = sch.recurrence;
    const day = startOfDay(date);
    if (!rec) { if (start && sameDate(start, day)) return [start, end]; return null; }
    const until = parseDt(rec.until, { endOfDay: true });
    if (until && day > startOfDay(until)) return null;
    if ((rec.skip_dates || []).indexOf(dateStr(day)) >= 0) return null;
    if (start && day < startOfDay(start)) return null;
    let cronTime = null;
    if (rec.weekly) { if (rec.weekly.indexOf(dayKeyName(day)) < 0) return null; }
    else if (rec.daily != null) {
      const n = rec.daily;
      const interval = (typeof n === "number" && n > 0) ? n : 1;
      const base = start ? startOfDay(start) : day;
      const diff = Math.round((day - base) / 86400000);
      if (diff % interval !== 0) return null;
    } else if (rec.monthly != null) {
      let days = rec.monthly;
      if (days && typeof days === "object" && !Array.isArray(days)) days = (days.day != null) ? [days.day] : [];
      if (typeof days === "number" || typeof days === "string") days = [days];
      const norm = [];
      for (const d of (days || [])) {
        if (d === "last" || d === "Last" || d === -1) norm.push(lastDayOfMonth(day.getFullYear(), day.getMonth() + 1));
        else { const v = parseInt(d, 10); if (!isNaN(v)) norm.push(v); }
      }
      if (norm.indexOf(day.getDate()) < 0) return null;
    } else if (rec.cron) { const r = cronMatchDate(rec.cron, day); if (!r[0]) return null; cronTime = r[1]; }
    else return null;
    const rtime = rec.time || {};
    let sh, sm;
    if (cronTime) { sh = cronTime[0]; sm = cronTime[1]; }
    else { const src = rtime.start ? parseDt(rtime.start) : start; sh = src ? src.getHours() : 0; sm = src ? src.getMinutes() : 0; }
    const occStart = new Date(day.getFullYear(), day.getMonth(), day.getDate(), sh, sm);
    let occEnd = null;
    const endSrc = rtime.end ? parseDt(rtime.end) : end;
    if (endSrc) occEnd = new Date(day.getFullYear(), day.getMonth(), day.getDate(), endSrc.getHours(), endSrc.getMinutes());
    return [occStart, occEnd];
  }
  function iterOccurrences(plan, rangeStart, rangeEnd) {
    const out = [];
    let d = startOfDay(rangeStart);
    const d1 = startOfDay(rangeEnd);
    while (d <= d1) { const occ = occurrenceOn(plan, d); if (occ) out.push([new Date(d), occ[0], occ[1]]); d = addDays(d, 1); }
    return out;
  }
  function isDelayed(plan, now, occurrenceDate, state) {
    const sch = schedule(plan);
    let endDt, d = null;
    if (sch.recurrence) { d = occurrenceDate || startOfDay(now); const occ = occurrenceOn(plan, d); endDt = occ ? occ[1] : null; }
    else { endDt = parseDt(sch.end, { endOfDay: true }); }
    if (!endDt) return false;
    return now > endDt && !isCompleted(plan, d, state);
  }

  // ===== TodoControl 相当: 状態 / 集計 / 子バーレイアウト / 状態遷移 =====
  function spanMinutes(start, end) { const s = parseDt(start), e = parseDt(end); if (s && e && e > s) return (e - s) / 60000; return 0; }
  function isInProgress(todo) { return !!(todo.start && !todo.end && !todo.complete); }
  function actualMinutes(todo, now) {
    const sessions = todo.work_sessions;
    if (Array.isArray(sessions) && sessions.length) {
      let total = 0, hasOpen = false;
      for (const s of sessions) {
        if (!s || typeof s !== "object") continue;
        if (!s.end) { hasOpen = true; if (now) total += spanMinutes(s.start, formatDt(now)); }
        else total += spanMinutes(s.start, s.end);
      }
      if (!hasOpen && isInProgress(todo) && now) total += spanMinutes(todo.start, formatDt(now));
      return total;
    }
    if (isInProgress(todo) && now) return spanMinutes(todo.start, formatDt(now));
    return spanMinutes(todo.start, todo.end);
  }
  function todoStatus(todo) {
    if (todo.complete) return "done";
    const st = todo.status;
    if (["todo", "in_progress", "paused", "done", "blocked"].indexOf(st) >= 0) return st;
    if (todo.blocked) return "blocked";
    if (isInProgress(todo)) return "in_progress";
    if (todo.work_sessions && todo.work_sessions.length) return "paused";
    return "todo";
  }
  function todoProgress(todo) {
    if (todo.complete) return 100;
    const p = todo.progress;
    if (typeof p === "number") return Math.max(0, Math.min(100, Math.trunc(p)));
    return 0;
  }
  function todoEstimateMin(todo, def) {
    def = def || 0;
    const e = todo.estimate_min;
    if (typeof e === "number" && e > 0) return e;
    const a = actualMinutes(todo);
    return a > 0 ? a : def;
  }
  function plannedTotalMin(plan, defPer) { defPer = defPer || 0; return (plan.todo || []).reduce((s, t) => s + todoEstimateMin(t, defPer), 0); }
  function scheduleCapacityMin(plan) {
    const sch = schedule(plan);
    const s = parseDt(sch.start), e = parseDt(sch.end, { endOfDay: true });
    if (s && e && e > s) return (e - s) / 60000;
    return null;
  }
  function overflowInfo(plan) {
    const cap = scheduleCapacityMin(plan);
    const planned = plannedTotalMin(plan);
    if (cap == null || planned <= 0) return null;
    return { capacity_min: cap, planned_min: planned, over: planned > cap, over_min: Math.max(0, planned - cap) };
  }
  function sessionSummary(todo, now) {
    let sessions = (todo.work_sessions || []).slice();
    if (!sessions.length && (todo.start || todo.end)) sessions = [{ start: todo.start, end: todo.end }];
    const parts = [];
    sessions.forEach((s, i) => {
      const sd = parseDt(s.start);
      if (!sd) return;
      const ed = parseDt(s.end);
      let mins, ee;
      if (ed) { mins = Math.max(0, (ed - sd) / 60000); ee = formatDt(ed); }
      else { mins = now ? (now - sd) / 60000 : 0; ee = "（作業中）"; }
      parts.push(`作業期間${i + 1}: ${formatDt(sd)}〜${ee} (実作業 ${Math.round(mins / 6) / 10}H)`);
    });
    return parts.join(", ");
  }
  function layoutTodos(plan, parentStart, parentEnd, now, defaultMin) {
    defaultMin = defaultMin || 60;
    const todos = plan.todo || [];
    const out = [];
    // 期限のない(開始も終了も明示なし)Todoは、その階層の区間[segStart,segEnd]を
    // 件数で等分して並べる（完了済みの実績時刻に引きずられて現在時刻付近から
    // 表示される問題を回避）。明示的な start/end を持つTodoはその時刻を使う。
    function walk(items, segStart, segEnd, prefix, depth) {
      const bounded = (segStart != null && segEnd != null && (segEnd.getTime() - segStart.getTime()) > 0);
      let autoCount = 0;
      for (const t of items) {
        if (t && typeof t === "object" && parseDt(t.start) == null && parseDt(t.end) == null) autoCount++;
      }
      const slice = (bounded && autoCount > 0) ? (segEnd.getTime() - segStart.getTime()) / autoCount : null;
      let autoIdx = 0;
      let cursor = segStart;
      items.forEach((t, idx) => {
        if (!t || typeof t !== "object") return;
        const path = prefix.concat([idx]);
        const s = parseDt(t.start);
        const e = parseDt(t.end, { endOfDay: true });
        const est = todoEstimateMin(t, 0);
        // 実績（work_sessions）の集計を先に行う。記録された作業期間があれば、それを
        // バー位置に採用する（「完了」押下時刻=t.end に引きずられず、「作業期間の手動編集」
        // での後日修正もそのままバーへ反映される）。
        const aStarts = [], aEnds = [];
        let openSession = false;
        for (const ws of (t.work_sessions || [])) {
          if (!ws || typeof ws !== "object") continue;
          const a = parseDt(ws.start), b = parseDt(ws.end);
          if (a) aStarts.push(a);
          if (b) aEnds.push(b); else if (a) openSession = true;
        }
        const hasSessions = aStarts.length > 0;
        const sesStart = hasSessions ? new Date(Math.min.apply(null, aStarts)) : null;
        let sesEnd = aEnds.length ? new Date(Math.max.apply(null, aEnds)) : null;
        if (openSession && now) sesEnd = (sesEnd != null && sesEnd > now) ? sesEnd : now;  // 作業中は now まで
        let ps, pe;
        if (hasSessions) {
          ps = sesStart; pe = sesEnd;          // 作業期間（実績）でバーを描く
        } else if (s != null || e != null) {
          ps = (s != null) ? s : cursor;
          if (e != null) pe = e;
          else if (ps != null && est > 0) pe = new Date(ps.getTime() + est * 60000);
          else if (ps != null && segEnd != null) pe = new Date(ps.getTime() + defaultMin * 60000);
          else pe = null;
        } else if (slice != null) {
          ps = new Date(segStart.getTime() + autoIdx * slice);
          pe = new Date(segStart.getTime() + (autoIdx + 1) * slice);
          autoIdx++;
        } else {
          ps = cursor;
          if (ps != null && est > 0) pe = new Date(ps.getTime() + est * 60000);
          else if (ps != null && segEnd != null) pe = new Date(ps.getTime() + defaultMin * 60000);
          else pe = null;
        }
        if (pe != null) cursor = pe;
        const milestone = pe == null;
        // actual_*（実績バー）は従来通り work_sessions 優先、無ければ start/end でフォールバック。
        if (!aStarts.length && s != null) aStarts.push(s);
        if (!aEnds.length && e != null) aEnds.push(e);
        out.push({
          todo_index: path[0], path: path, depth: depth,
          name: t.name || `todo${idx + 1}`, assignee: t.assignee || "",
          status: todoStatus(t), memo: t.text || "", progress: todoProgress(t),
          start: ps, end: pe, has_own_schedule: (hasSessions || s != null || e != null),
          actual_start: aStarts.length ? new Date(Math.min.apply(null, aStarts)) : null,
          actual_end: aEnds.length ? new Date(Math.max.apply(null, aEnds)) : null,
          estimate_min: est, actual_min: actualMinutes(t, now), milestone: milestone,
        });
        if (t.children && t.children.length) walk(t.children, ps, pe, path, depth + 1);
      });
    }
    walk(todos, parentStart, parentEnd, [], 0);
    return out;
  }
  function countTodosDeep(todos) {
    let done = 0, total = 0, prog = 0;
    for (const t of (todos || [])) {
      if (!t || typeof t !== "object") continue;
      total++;
      if (t.complete) done++;
      else if (t.start && !t.end) prog++;
      const r = countTodosDeep(t.children || []);
      done += r[0]; total += r[1]; prog += r[2];
    }
    return [done, total, prog];
  }
  function openSession(todo, now) {
    const sessions = (todo.work_sessions || []).map(s => Object.assign({}, s));
    if (!(sessions.length && !sessions[sessions.length - 1].end)) sessions.push({ start: formatDt(now), end: "", note: "" });
    return sessions;
  }
  function closeOpenSession(sessions, now, note) {
    if (sessions.length && !sessions[sessions.length - 1].end) { sessions[sessions.length - 1].end = formatDt(now); if (note) sessions[sessions.length - 1].note = note; }
    return sessions;
  }
  function startSession(todo, now, memo) {
    const t = Object.assign({}, todo);
    const sessions = openSession(t, now);
    if (memo) sessions[sessions.length - 1].note = memo;
    t.work_sessions = sessions;
    t.status = "in_progress"; t.complete = false;
    t.start = todo.start || formatDt(now); t.end = "";
    t.actual_min = actualMinutes(t, now);
    return t;
  }
  function pauseSession(todo, now, memo) {
    const t = Object.assign({}, todo);
    let sessions = (t.work_sessions || []).map(s => Object.assign({}, s));
    if (!(sessions.length && !sessions[sessions.length - 1].end) && todo.start) sessions.push({ start: todo.start, end: "", note: "" });
    sessions = closeOpenSession(sessions, now, memo);
    t.work_sessions = sessions;
    t.status = "paused"; t.start = "";
    t.actual_min = actualMinutes(t, now);
    return t;
  }
  function completeSession(todo, now, memo) {
    const t = pauseSession(todo, now, memo);
    t.status = "done"; t.complete = true; t.end = formatDt(now); t.progress = 100;
    t.actual_min = actualMinutes(t, now);
    return t;
  }
  function resetSession(todo, now, memo) {
    const t = Object.assign({}, todo);
    let sessions = (t.work_sessions || []).map(s => Object.assign({}, s));
    if (sessions.length && !sessions[sessions.length - 1].end && now) sessions = closeOpenSession(sessions, now, memo);
    t.work_sessions = sessions;
    t.status = "todo"; t.complete = false; t.start = ""; t.end = "";
    if (memo) t.text = memo;
    return t;
  }

  // ===== GanttViewModel 相当: window / build_models =====
  function meta(plan, key, def) {
    if (plan && typeof plan === "object" && key in plan) return plan[key];
    const s = plan.settings;
    if (s && typeof s === "object" && key in s) return s[key];
    return def;
  }
  function ganttWindow(now, rangeKey, offset) {
    rangeKey = rangeKey || "week"; offset = offset || 0;
    let d = startOfDay(now);
    let start, end;
    if (rangeKey === "day") { d = addDays(d, offset); start = d; end = d; }
    else if (rangeKey === "month") {
      const base = new Date(d.getFullYear(), d.getMonth(), 1);
      const m = base.getMonth() + offset;
      start = new Date(base.getFullYear(), m, 1);
      end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
    } else {
      const wd = (d.getDay() + 6) % 7;
      start = addDays(d, -wd + 7 * offset);
      end = addDays(start, 6);
    }
    return [new Date(start.getFullYear(), start.getMonth(), start.getDate(), 0, 0),
    new Date(end.getFullYear(), end.getMonth(), end.getDate(), 23, 59)];
  }
  function progressOf(plan, done) {
    if (done) return 100;
    // 手動値: schedule.progress 優先 → 無ければ管理メタ progress
    const sch = schedule(plan);
    let p = (typeof sch.progress === "number") ? sch.progress : meta(plan, "progress");
    if (typeof p === "number") return Math.max(0, Math.min(100, Math.trunc(p)));
    // 自動: 子タスク(todo, children 含む)の完了率
    const todos = plan.todo || [];
    if (todos.length) { const c = countTodosDeep(todos); if (c[1]) return Math.round(100 * c[0] / c[1]); }
    const cl = meta(plan, "checklist");
    if (Array.isArray(cl) && cl.length) { const d = cl.filter(x => x && typeof x === "object" && x.done).length; return Math.round(100 * d / cl.length); }
    return 0;
  }
  function makeBar(plan, occDate, sdt, edt, now, state, runningNames) {
    const recurring = !!schedule(plan).recurrence;
    const occKey = recurring ? occDate : null;
    const done = isCompleted(plan, occKey, state);
    const delayed = isDelayed(plan, now, occKey, state);
    const est = meta(plan, "estimate_min");
    let milestone = false;
    if (edt == null) {
      if (sdt != null && typeof est === "number" && est > 0) edt = new Date(sdt.getTime() + est * 60000);
      else milestone = true;
    }
    const name = plan.name || "";
    const prog = progressOf(plan, done);
    // 進捗率 100%（子タスク全完了 or 手動 100）は「実質完了」として完了扱い。
    // ステータスは子の進捗率から判定する方針に沿い、明示的な完了記録
    // （schedule.completion）が無くても 100% なら done として元のスケジュール区間で
    // 描く（遅延延長しない）。正式な完了記録・通知には影響しない（描画判定のみ）。
    const effDone = done || prog >= 100;
    // スケジュール健全性（実進捗% と 経過時間% の単純比較）
    let status;
    if (effDone) status = "done";
    else if (edt != null && now > edt) status = "delayed";           // end 超過で未完
    else if (sdt != null && edt != null && edt > sdt) {
      let elapsed = (now - sdt) / (edt - sdt) * 100;
      elapsed = Math.max(0, Math.min(100, elapsed));
      status = (prog >= elapsed) ? "on_schedule" : "at_risk";
    } else status = "on_schedule";                                    // 開始前・日付不足は順調扱い
    const rec = (state || {})[name] || {};
    let actualStart, actualEnd;
    if (recurring) { const orec = (rec.occurrences || {})[sdt ? dateStr(sdt) : ""] || {}; actualStart = orec.actual_start; actualEnd = orec.completion; }
    else { actualStart = rec.actual_start || schedule(plan).actual_start; actualEnd = rec.completion || schedule(plan).completion; }
    // ── 期限切れ延長（delayed かつ未完了）─────────────────────────────────
    // end(期限)が過去かつ未完了のとき、バーを現在時刻まで延ばして表示する。
    // 実際の作業遅れはスケジュール(Plan)ではなく Todo 側で記録する考え方のため、
    // 「完了」した Plan はここでは延長しない（下の actual_end クランプ参照）。
    let delayEnd = null;
    if (status === "delayed" && !effDone && edt != null && now > edt) delayEnd = now;
    let actualEndDt = actualEnd ? parseDt(actualEnd) : null;
    // completion が "done" 等の非日付 truthy 文字列の場合 parse が null になる。
    // 完了済み（進捗100%含む）なら計画終了(edt)で代用し、実績バーが現在まで伸びないようにする。
    if (effDone && actualEndDt == null) actualEndDt = edt;
    // 完了した Plan は「元々のスケジュール区間」を描く。実績完了が予定終了より
    // 後（遅れて完了）でもバーを now まで延ばさない（実作業の遅れは子 Todo で記録）。
    else if (effDone && actualEndDt != null && edt != null && actualEndDt > edt) actualEndDt = edt;
    return {
      start: sdt, end: edt,
      delay_end: delayEnd,
      actual_start: actualStart ? parseDt(actualStart) : null,
      actual_end: actualEndDt,
      status: status, progress: prog, milestone: milestone,
    };
  }
  function buildModels(plans, now, opts) {
    opts = opts || {};
    const state = opts.state || null;
    const runningNames = opts.runningNames || new Set();
    const rangeKey = opts.rangeKey || "week";
    const offset = opts.offset || 0;
    const showTodos = !!opts.showTodos;
    const win = ganttWindow(now, rangeKey, offset);
    const winS = win[0], winE = win[1];
    function sortKey(p) { const order = meta(p, "order"); return [meta(p, "pin") ? 0 : 1, (typeof order === "number") ? order : 1000000, p.name || ""]; }
    const sorted = plans.slice().sort((a, b) => {
      const ka = sortKey(a), kb = sortKey(b);
      for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; }
      return 0;
    });
    const rows = [], bars = [];
    for (const plan of sorted) {
      const kind = (plan.task_kind === "human" || plan.type === "todo") ? "human" : "pc";
      const rowIdx = rows.length;
      let hasBar = false;
      const sch = schedule(plan);
      const recurring = !!sch.recurrence;
      let psd = null, ped = null, occs = [];
      if (recurring) { occs = iterOccurrences(plan, winS, winE); }
      else {
        psd = parseDt(sch.start); ped = parseDt(sch.end, { endOfDay: true });
        const spanS = psd || ped, spanE = ped || psd;
        if (spanS != null && spanE != null) {
          // 通常: 窓と重なる場合
          const inWindow = spanE >= winS && spanS <= winE;
          // 期限切れ延長: 期限が窓より前でも、未完了で now が窓内なら遅延バーを出す
          const overdueIntoWindow = spanE < winS && now >= winS && !isCompleted(plan, null, state);
          if (inWindow || overdueIntoWindow) occs = [[psd ? startOfDay(psd) : startOfDay(spanE), psd, ped]];
        }
      }
      for (const o of occs) {
        const bar = makeBar(plan, o[0], o[1], o[2], now, state, runningNames);
        bar.row = rowIdx; bar.plan_name = plan.name || ""; bar.child = false;
        bars.push(bar); hasBar = true;
      }
      const todos = plan.todo || [];
      const hasSchedule = !!(recurring || psd != null || ped != null);
      // Python版に合わせ、スケジュール設定済みのPlanのみ Todo を展開（未設定は
      // 「スケジュールなし」セクションへ。gantt.html の renderUnscheduled が表示）。
      const wantTodos = !recurring && todos.length && showTodos && hasSchedule;
      if (hasBar || wantTodos) {
        const c = countTodosDeep(todos);
        let rowName = plan.name || "";
        if (c[2]) rowName += `  ☑${c[2]}`;
        else if (c[1]) rowName += `  ${c[0]}/${c[1]}`;
        if (!hasBar) rowName += "  （予定未設定）";
        const ov = overflowInfo(plan);
        const over = !!(ov && ov.over);
        if (over) rowName += "  ⚠超過";
        rows.push({
          plan_list: plan._plan_list || plan._file || "", name: rowName,
          plan_name: plan.name || "", kind: kind,
          priority: meta(plan, "priority", "normal"), order: meta(plan, "order"),
          pin: !!meta(plan, "pin"), tags: meta(plan, "tags", []),
          over: over, level: 0, child: false,
        });
        if (wantTodos) {
          // 基準は表示中ウィンドウ（Python版 build_models 準拠：win_s/win_e）。
          const pStart = psd || winS, pEnd = ped || winE;
          const planOverdue = (ped != null && now > ped && !isCompleted(plan, null, state));
          const allCt = layoutTodos(plan, pStart, pEnd, now);
          // 未完了・無期限Todoは now〜Plan終了 を件数で等分したスロットに配置。
          const planEndForSlots = (ped != null && ped > now) ? ped : null;
          let nNsi = 0;
          for (const ct of allCt) { if (!ct.has_own_schedule && ct.status !== "done") nNsi++; }
          let slotMs = null;
          if (nNsi > 0 && planEndForSlots != null) slotMs = (planEndForSlots.getTime() - now.getTime()) / nNsi;
          let nsiSlotIdx = 0;
          for (const ct of allCt) {
            const noSchedule = !ct.has_own_schedule;
            let tStatus = ct.status, delayEnd = null, isMilestone = ct.milestone, tStart, tEnd;
            if (noSchedule) {
              if (tStatus === "done") {
                // 完了済みの無期限Todoは Plan 開始にマイルストーン（窓外は非表示）。
                if (psd == null || !(winS <= psd && psd <= winE)) continue;
                tStart = psd; tEnd = null; isMilestone = true;
              } else if (slotMs != null) {
                tStart = new Date(now.getTime() + slotMs * nsiSlotIdx);
                tEnd = new Date(now.getTime() + slotMs * (nsiSlotIdx + 1));
                nsiSlotIdx++; isMilestone = false;
              } else {
                // 未完了 & Plan終了が過去/無し → 遅延扱い。
                tStart = ct.start || now; tEnd = ct.end;
                if (planOverdue) { delayEnd = now; tStatus = "delayed"; }
              }
            } else {
              if (ct.start == null) continue;
              tStart = ct.start; tEnd = ct.end;
              if (tStatus !== "done") {
                if (ct.end != null && now > ct.end) { delayEnd = now; tStatus = "delayed"; }       // (a) Todo自身が期限切れ
                else if (ct.end == null && planOverdue) { delayEnd = now; tStatus = "delayed"; }    // (b) 親Plan期限切れ&Todo無期限
              }
            }
            const crow = rows.length;
            const depth = ct.depth || 0;
            let cname = "   ".repeat(depth + 1) + "└ " + ct.name;
            if (ct.assignee) cname += `  @${ct.assignee}`;
            rows.push({
              plan_list: plan._plan_list || plan._file || "", name: cname,
              plan_name: plan.name || "", kind: kind, todo_index: ct.todo_index,
              path: ct.path, priority: meta(plan, "priority", "normal"),
              order: meta(plan, "order"), pin: false, tags: [], over: false,
              level: depth + 1, child: true,
            });
            let prog = ct.progress;
            if (prog == null) prog = tStatus === "done" ? 100 : 0;
            bars.push({
              row: crow, child: true, plan_name: plan.name || "",
              todo_index: ct.todo_index, path: ct.path, depth: depth,
              start: tStart, end: tEnd, delay_end: delayEnd,
              actual_start: ct.actual_start, actual_end: ct.actual_end,
              status: tStatus, progress: prog, milestone: isMilestone, no_schedule: noSchedule,
            });
          }
        }
      }
    }
    return { range: rangeKey, window: { start: winS, end: winE }, now: now, rows: rows, bars: bars };
  }

  // ===== PlanRisk 相当: リスク判定 / 時間集計 =====
  function formatDuration(secs) {
    secs = Math.trunc(secs);
    const totalMin = Math.trunc(secs / 60);
    const h = Math.trunc(totalMin / 60), m = totalMin % 60;
    if (h) return `${h}時間${pad2(m)}分`;
    return `${m}分`;
  }
  function todoActualSecs(todo) {
    const sessions = todo.work_sessions;
    if (Array.isArray(sessions) && sessions.length) {
      let total = 0, any = false;
      for (const ws of sessions) {
        if (!ws || typeof ws !== "object") continue;
        const s = parseDt(ws.start), e = parseDt(ws.end);
        if (s && e && e > s) { total += (e - s) / 1000; any = true; }
      }
      if (any) return total;
    }
    const s = parseDt(todo.start), e = parseDt(todo.end);
    if (s && e && e > s) return (e - s) / 1000;
    return null;
  }
  function todoElapsedSummary(todos) {
    let total = 0, trouble = 0, recorded = 0;
    const incomplete = [], troubleIncomplete = [];
    for (const t of (todos || [])) {
      const secs = todoActualSecs(t);
      if (secs != null) { total += secs; recorded++; if (t.type === "trouble_shoot") trouble += secs; }
      if (!t.complete) { incomplete.push(t.name || ""); if (t.type === "trouble_shoot") troubleIncomplete.push(t.name || ""); }
    }
    return { total_actual_secs: total, recorded_count: recorded, trouble_secs: trouble, incomplete_names: incomplete, trouble_incomplete: troubleIncomplete };
  }
  function checkRisks(plan, now) {
    now = now || new Date();
    const w = [];
    const sch = plan.schedule || {};
    const todos = plan.todo || [];
    const complete = !!plan.complete || !!sch.completion;
    const deadline = parseDt(sch.end);
    const sStart = parseDt(sch.start);
    if (deadline && !complete && now > deadline) w.push({ code: "deadline_over", level: "error", message: `期限超過: ${formatDuration((now - deadline) / 1000)} 経過` });
    const settings = plan.settings || {};
    const estMin = (plan.estimate_min != null) ? plan.estimate_min : settings.estimate_min;
    if (estMin && deadline && sStart) { const avail = (deadline - sStart) / 1000, est = estMin * 60; if (est > avail) w.push({ code: "estimate_over", level: "warning", message: `見積もり超過: 見積 ${formatDuration(est)} > スケジュール ${formatDuration(avail)}` }); }
    const summary = todoElapsedSummary(todos);
    const actualSecs = summary.total_actual_secs;
    if (actualSecs && deadline && sStart) { const avail = (deadline - sStart) / 1000; if (actualSecs > avail) w.push({ code: "todo_time_over", level: "warning", message: `実績超過: 合計 ${formatDuration(actualSecs)} > スケジュール ${formatDuration(avail)}` }); }
    if (summary.trouble_incomplete.length) w.push({ code: "unresolved_trouble", level: "warning", message: `未解決トラブル: ${summary.trouble_incomplete.slice(0, 3).join("、")}` });
    if (deadline && !complete && now < deadline) {
      const remaining = (deadline - now) / 1000;
      const recAvg = summary.recorded_count ? actualSecs / summary.recorded_count : 0;
      const incN = summary.incomplete_names.length;
      const estRem = recAvg ? incN * recAvg : 0;
      if (estRem && estRem > remaining) w.push({ code: "schedule_risk_high", level: "error", message: `スケジュールリスク高: 残 ${incN}件 (${formatDuration(estRem)}) > 残期限 ${formatDuration(remaining)}` });
    }
    return w;
  }
  function riskLevel(plan, now) {
    const ws = checkRisks(plan, now);
    if (ws.some(x => x.level === "error")) return "error";
    if (ws.some(x => x.level === "warning")) return "warning";
    return "ok";
  }

  // ===== PlanStore 相当: PlanList JSON の CRUD（{name:plan} / {name:[plans]} 両対応）=====
  function* iterPlans(obj) {
    if (!obj || typeof obj !== "object") return;
    for (const key of Object.keys(obj)) {
      const value = obj[key];
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const name = value.name != null ? value.name : key;
        yield { container: obj, key: key, value: value, name: name };
      } else if (Array.isArray(value)) {
        for (let i = 0; i < value.length; i++) { const el = value[i]; if (el && typeof el === "object") yield { container: value, key: i, value: el, name: el.name }; }
      }
    }
  }
  function listNames(obj) { const out = []; for (const it of iterPlans(obj)) if (it.name) out.push(it.name); return out; }
  function getPlan(obj, name) {
    for (const it of iterPlans(obj)) if (it.name === name) { const p = Object.assign({}, it.value); if (p.name == null) p.name = name; return p; }
    return null;
  }
  function stripInternal(plan) {
    if (!plan || typeof plan !== "object") return plan;
    const out = {};
    for (const k of Object.keys(plan)) if (!(typeof k === "string" && k.startsWith("_"))) out[k] = plan[k];
    return out;
  }
  function setIn(obj, name, plan) { for (const it of iterPlans(obj)) if (it.name === name) { it.container[it.key] = plan; return true; } return false; }
  function upsertPlan(obj, plan) {
    const name = plan.name;
    if (!name) return false;
    const clean = stripInternal(plan);
    if (!setIn(obj, name, clean)) obj[name] = clean;
    return true;
  }
  function deletePlan(obj, name) {
    let removed = false;
    for (const key of Object.keys(obj)) { const v = obj[key]; if (key === name || (v && typeof v === "object" && !Array.isArray(v) && v.name === name)) { delete obj[key]; removed = true; } }
    for (const key of Object.keys(obj)) { const v = obj[key]; if (Array.isArray(v)) { const nv = v.filter(el => !(el && typeof el === "object" && el.name === name)); if (nv.length !== v.length) { obj[key] = nv; removed = true; } } }
    return removed;
  }
  function deepCopy(x) { return JSON.parse(JSON.stringify(x)); }
  function duplicatePlan(obj, name, newName) {
    const src = getPlan(obj, name);
    if (!src) return false;
    const dup = deepCopy(stripInternal(src));
    dup.name = newName || `${name} (copy)`;
    if (dup.schedule && typeof dup.schedule === "object") { delete dup.schedule.completion; delete dup.schedule.actual_start; }
    return upsertPlan(obj, dup);
  }
  function loadPlansFlat(files) {
    const out = [];
    for (const f of (files || [])) {
      const obj = f.data;
      if (!obj || typeof obj !== "object") continue;
      for (const name of Object.keys(obj)) {
        const value = obj[name];
        if (value && typeof value === "object" && !Array.isArray(value)) { const p = Object.assign({}, value); if (p.name == null) p.name = name; p._file = f.label; p._plan_list = name; out.push(p); }
        else if (Array.isArray(value)) { for (const el of value) if (el && typeof el === "object") { const p = Object.assign({}, el); p._file = f.label; p._plan_list = name; out.push(p); } }
      }
    }
    return out;
  }
  function newPlanTemplate(name, kind) {
    name = name || "新しいPlan"; kind = kind || "todo";
    if (kind === "todo") return { name: name, type: "todo", text: "", todo: [], schedule: { start: "", end: "", completion: "" }, settings: {} };
    return { name: name, type: "ExecuteProgram", schedule: { start: "", end: "", completion: "" }, settings: {} };
  }
  function saveAsTemplate(obj, plan) {
    const tmpl = deepCopy(stripInternal(plan));
    for (const t of (tmpl.todo || [])) { delete t.start; delete t.end; t.complete = false; }
    delete tmpl.complete;
    if (tmpl.schedule && typeof tmpl.schedule === "object") { delete tmpl.schedule.completion; delete tmpl.schedule.actual_start; }
    return upsertPlan(obj, tmpl);
  }
  function createFromTemplate(tmpl, sessionName) {
    if (!tmpl) return null;
    const plan = deepCopy(stripInternal(tmpl));
    plan.name = sessionName || tmpl.name;
    plan.template = tmpl.name;
    for (const t of (plan.todo || [])) { delete t.start; delete t.end; t.complete = false; }
    delete plan.complete;
    if (plan.schedule && typeof plan.schedule === "object") delete plan.schedule.completion;
    return plan;
  }

  // ===== WorkReport 相当: 期間作業報告テキスト =====
  function dtInPeriod(dt, pStart, pEnd) { if (!dt) return false; if (pStart && dt < pStart) return false; if (pEnd && dt > pEnd) return false; return true; }
  function planInPeriod(plan, pStart, pEnd) {
    const sch = plan.schedule || {};
    if (dtInPeriod(parseDt(sch.completion), pStart, pEnd)) return true;
    if (dtInPeriod(parseDt(sch.actual_start), pStart, pEnd)) return true;
    for (const s of (plan.work_sessions || [])) if (dtInPeriod(parseDt(s.start), pStart, pEnd)) return true;
    for (const t of (plan.todo || [])) if (dtInPeriod(parseDt(t.start), pStart, pEnd)) return true;
    const sStart = parseDt(sch.start), sEnd = parseDt(sch.end);
    if (sStart && sEnd) { if (pEnd && sStart > pEnd) return false; if (pStart && sEnd < pStart) return false; return true; }
    return false;
  }
  function sessionTotalSecsInPeriod(plan, pStart, pEnd) {
    let total = 0;
    for (const s of (plan.work_sessions || [])) {
      if (dtInPeriod(parseDt(s.start), pStart, pEnd)) { const a = parseDt(s.start), b = parseDt(s.end); if (a && b && b > a) total += (b - a) / 1000; }
    }
    return total;
  }
  function generateReport(plans, periodStartStr, periodEndStr) {
    const pStart = parseDt(periodStartStr), pEnd = parseDt(periodEndStr);
    const lines = [];
    lines.push(`【作業報告】 ${periodStartStr} 〜 ${periodEndStr}`);
    lines.push("");
    const active = plans.filter(p => planInPeriod(p, pStart, pEnd));
    let totalSecs = 0, completedCount = 0, ongoingCount = 0;
    for (const plan of active) {
      const sch = plan.schedule || {};
      // ガントの実質完了(eff_done)と揃える: 明示完了に加え、進捗100%（子Todo全完了/
      // 手動100）も完了として報告する。完了Planが「継続中」と書かれる不具合の修正。
      const isDone = !!plan.complete || !!sch.completion || progressOf(plan, false) >= 100;
      const marker = isDone ? "■" : "□";
      const suffix = isDone ? "　→ 完了" : "（継続中）";
      if (isDone) completedCount++; else ongoingCount++;
      lines.push(`${marker} ${plan.name || ""}${suffix}`);
      const planText = (plan.text || "").trim();
      if (planText) planText.split(/\r?\n/).forEach(tl => { if (tl.trim()) lines.push(`    ${tl.trim()}`); });
      for (const todo of (plan.todo || [])) {
        // complete フラグだけでなく status:"done" / 進捗100% も完了とみなす。
        const tDone = todoStatus(todo) === "done" || todoProgress(todo) >= 100;
        const tMarker = tDone ? "  ●" : "  ○";
        let tSuffix = tDone ? " → 完了" : "";
        if (!tDone && todo.start && !todo.end) tSuffix = "（作業中）";
        const tType = todo.type || "";
        const typeTag = (tType && tType !== "normal") ? `  [${tType}]` : "";
        lines.push(`${tMarker} ${todo.name || ""}${typeTag}${tSuffix}`);
        const tText = (todo.text || "").trim();
        if (tText) tText.split(/\r?\n/).forEach(sub => { const s = sub.trim(); if (s) lines.push(`      ・${s}`); });
      }
      const secs = sessionTotalSecsInPeriod(plan, pStart, pEnd);
      if (secs) { totalSecs += secs; lines.push(`    └ 作業時間: ${formatDuration(secs)}`); }
      lines.push("");
    }
    if (!active.length) { lines.push("（期間内に該当する作業はありません）"); lines.push(""); }
    lines.push("─".repeat(40));
    if (totalSecs) lines.push(`作業セッション合計: ${formatDuration(totalSecs)}`);
    lines.push(`期間内完了: ${completedCount}件 / 継続中: ${ongoingCount}件`);
    return lines.join("\n");
  }

  return {
    parseDt, formatDt, dateStr, addDays, startOfDay, pad2,
    isCompleted, occurrenceOn, iterOccurrences, isDelayed, isKnownNoActionType,
    actualMinutes, isInProgress, todoStatus, todoProgress, todoEstimateMin,
    plannedTotalMin, scheduleCapacityMin, overflowInfo, sessionSummary,
    layoutTodos, countTodosDeep, startSession, pauseSession, completeSession, resetSession,
    ganttWindow, buildModels, meta,
    formatDuration, todoActualSecs, todoElapsedSummary, checkRisks, riskLevel,
    iterPlans, listNames, getPlan, upsertPlan, deletePlan, duplicatePlan,
    loadPlansFlat, newPlanTemplate, saveAsTemplate, createFromTemplate, stripInternal, deepCopy,
    generateReport, planInPeriod,
  };
});
