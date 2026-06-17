import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';

const B = `${environment.apiBase}/api/v1`;

export interface Church { id: number; name: string; }
export interface Group { id: number; church_id: number; name: string; meeting_day?: string | null; }
export interface Leader { id: number; bsg_id: number; name: string; telegram_user_id?: number | null; telegram_linked_at?: any; }
export interface Member {
  id: number; bsg_id: number; name: string; surname?: string | null;
  mobile_number?: string | null; city_id?: number | null; street_id?: number | null;
  city_name?: string | null; street_name?: string | null; status: string; photo_count: number;
}
export interface City { id: number; name: string; }
export interface Street { id: number; city_id: number; name: string; }
export interface DirectoryRow { id: number; name: string; surname?: string | null; bsg_id: number; bsg_name: string; is_own_group: boolean; }
export interface AppSettings {
  telegram_bot_token?: string | null; telegram_token_set?: boolean;
  telegram_match_field?: string | null; telegram_reply_mode?: string | null;
  face_match_threshold?: number; face_det_score_min?: number; face_min_pixels?: number;
  face_max_yaw_deg?: number; face_blur_var_min?: number; discard_low_quality?: boolean;
}
export interface Visitor { id: number; meeting_id: number; bsg_id: number; meeting_date: string; status: string; crop_url?: string | null; created_at: string; }
export interface Suggestion { member_id: number; name: string; bsg_id: number; bsg_name: string; same_group: boolean; similarity: number; photo_url?: string | null; }
export interface RecognitionResult {
  bsg_id: number; bsg_name: string; meeting_id: number | null; faces_detected: number;
  recognized_members: { member_id: number; name: string; confidence: number }[];
  visitors: number;
  discarded: { reason: string; det_score: number; size_px: number; yaw_deg: number; blur_var: number }[];
  saved: boolean;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // ---- Setup (admin) ----
  churches() { return this.http.get<Church[]>(`${B}/setup/churches`); }
  createChurch(name: string) { return this.http.post<Church>(`${B}/setup/churches`, { name }); }
  groups(church_id?: number) {
    const q = church_id ? `?church_id=${church_id}` : '';
    return this.http.get<Group[]>(`${B}/setup/groups${q}`);
  }
  createGroup(b: { church_id: number; name: string; meeting_day?: string }) {
    return this.http.post<Group>(`${B}/setup/groups`, b);
  }
  leaders() { return this.http.get<Leader[]>(`${B}/setup/leaders`); }
  createLeader(b: { bsg_id: number; name: string; mobile_number: string; password: string }) {
    return this.http.post<Leader>(`${B}/setup/leaders`, b);
  }
  leaderLinkCode(leader_id: number) {
    return this.http.post<{ link_code: string; instructions: string }>(
      `${B}/setup/leaders/${leader_id}/telegram-link-code`, {});
  }
  deactivateLeader(leader_id: number) {
    return this.http.post<{ ok: boolean; freed_bsg_id: number }>(
      `${B}/setup/leaders/${leader_id}/deactivate`, {});
  }

  // ---- Admin settings (Telegram + recognition thresholds) ----
  getSettings() { return this.http.get<AppSettings>(`${B}/setup/settings`); }
  updateSettings(b: Partial<AppSettings> & { telegram_bot_token?: string }) {
    return this.http.put<AppSettings>(`${B}/setup/settings`, b);
  }

  // ---- Lookups (City / Street) ----
  cities() { return this.http.get<City[]>(`${B}/lookups/cities`); }
  createCity(name: string) { return this.http.post<City>(`${B}/lookups/cities`, { name }); }
  streets(city_id?: number) {
    const q = city_id ? `?city_id=${city_id}` : '';
    return this.http.get<Street[]>(`${B}/lookups/streets${q}`);
  }
  createStreet(city_id: number, name: string) {
    return this.http.post<Street>(`${B}/lookups/streets`, { city_id, name });
  }

  // ---- Members ----
  members(bsg_id?: number) {
    const q = bsg_id ? `?bsg_id=${bsg_id}` : '';
    return this.http.get<Member[]>(`${B}/members${q}`);
  }
  createMember(b: { name: string; surname?: string; mobile_number?: string; city_id?: number; street_id?: number; bsg_id?: number }) {
    return this.http.post<Member>(`${B}/members`, b);
  }
  updateMember(id: number, b: Partial<{ name: string; surname: string; mobile_number: string; city_id: number; street_id: number; status: string }>) {
    return this.http.patch<Member>(`${B}/members/${id}`, b);
  }
  addPhotos(member_id: number, files: File[]): Observable<Member> {
    const fd = new FormData();
    files.forEach((f) => fd.append('files', f));
    return this.http.post<Member>(`${B}/members/${member_id}/photos`, fd);
  }
  // Transfer / pull a member from another group into this leader's group.
  directory(q?: string) {
    const qs = q ? `?q=${encodeURIComponent(q)}` : '';
    return this.http.get<DirectoryRow[]>(`${B}/members/directory${qs}`);
  }
  transferMember(member_id: number, target_bsg_id?: number) {
    const qs = target_bsg_id ? `?target_bsg_id=${target_bsg_id}` : '';
    return this.http.post<Member>(`${B}/members/${member_id}/transfer${qs}`, {});
  }

  // ---- Recognition test ----
  testRecognition(bsg_id: number, file: File, persist: boolean) {
    const fd = new FormData();
    fd.set('bsg_id', String(bsg_id));
    fd.set('persist', String(persist));
    fd.set('file', file);
    return this.http.post<RecognitionResult>(`${B}/recognition/test`, fd);
  }

  // Load a protected image as an object URL (the auth interceptor adds the token;
  // a plain <img src> cannot send the Authorization header).
  imageObjectUrl(path: string): Observable<string> {
    const url = path.startsWith('http') ? path : `${environment.apiBase}${path}`;
    return this.http.get(url, { responseType: 'blob' }).pipe(map((b) => URL.createObjectURL(b)));
  }

  // ---- Visitors ----
  visitors() { return this.http.get<Visitor[]>(`${B}/visitors`); }
  suggestions(id: number) { return this.http.get<Suggestion[]>(`${B}/visitors/${id}/suggestions`); }
  mapVisitor(id: number, member_id: number, move_to_my_group: boolean) {
    return this.http.post<Visitor>(`${B}/visitors/${id}/map`, { member_id, move_to_my_group });
  }
  promoteVisitor(id: number, name: string, mobile_number?: string) {
    return this.http.post<Visitor>(`${B}/visitors/${id}/promote`, { name, mobile_number });
  }
  keepVisitor(id: number) { return this.http.post<Visitor>(`${B}/visitors/${id}/keep`, {}); }

  // ---- Reports ----
  groupAttendance(bsg_id?: number) { return this.http.get<any[]>(`${B}/reports/group-attendance${bsg_id ? '?bsg_id=' + bsg_id : ''}`); }
  memberAttendance(bsg_id?: number) { return this.http.get<any[]>(`${B}/reports/member-attendance${bsg_id ? '?bsg_id=' + bsg_id : ''}`); }
  visitorStats(bsg_id?: number) { return this.http.get<any>(`${B}/reports/visitor-stats${bsg_id ? '?bsg_id=' + bsg_id : ''}`); }
  growth(bsg_id?: number) { return this.http.get<any[]>(`${B}/reports/growth${bsg_id ? '?bsg_id=' + bsg_id : ''}`); }
  absentees(bsg_id?: number) { return this.http.get<any[]>(`${B}/reports/absentees${bsg_id ? '?bsg_id=' + bsg_id : ''}`); }
}
