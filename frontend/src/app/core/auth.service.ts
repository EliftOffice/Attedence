import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Token {
  access_token: string;
  token_type: string;
  role: 'admin' | 'leader';
  name: string;
  user_id: number;
}

export interface Me {
  user_id: number;
  name: string;
  role: 'admin' | 'leader';
  mobile_number: string;
  leader_bsg_id: number | null;
}

const TOKEN_KEY = 'attendance_token';
const ROLE_KEY = 'attendance_role';
const NAME_KEY = 'attendance_name';

@Injectable({ providedIn: 'root' })
export class AuthService {
  role = signal<string | null>(localStorage.getItem(ROLE_KEY));
  name = signal<string | null>(localStorage.getItem(NAME_KEY));

  constructor(private http: HttpClient) {}

  login(mobile_number: string, password: string): Observable<Token> {
    // Backend uses OAuth2 password form: `username` carries the mobile number.
    const body = new FormData();
    body.set('username', mobile_number);
    body.set('password', password);
    return this.http.post<Token>(`${environment.apiBase}/api/v1/auth/login`, body).pipe(
      tap((t) => {
        localStorage.setItem(TOKEN_KEY, t.access_token);
        localStorage.setItem(ROLE_KEY, t.role);
        localStorage.setItem(NAME_KEY, t.name);
        this.role.set(t.role);
        this.name.set(t.name);
      })
    );
  }

  me(): Observable<Me> {
    return this.http.get<Me>(`${environment.apiBase}/api/v1/auth/me`);
  }

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  get isLoggedIn(): boolean {
    return !!this.token;
  }

  get isAdmin(): boolean {
    return this.role() === 'admin';
  }

  logout(): void {
    localStorage.clear();
    this.role.set(null);
    this.name.set(null);
  }
}
