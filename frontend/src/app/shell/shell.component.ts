import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  styles: [`
    .layout { display: flex; min-height: 100vh; }
    nav { width: 220px; background: #1a202c; color: #cbd5e0; padding: 20px 0; }
    nav h3 { color: #fff; padding: 0 20px; font-size: 15px; }
    nav a { display: block; padding: 10px 20px; color: #cbd5e0; text-decoration: none; font-size: 14px; }
    nav a:hover, nav a.active { background: #2d3748; color: #fff; border-left: 3px solid var(--primary); }
    .content { flex: 1; padding: 24px; max-width: 1100px; }
    .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  `],
  template: `
    <div class="layout">
      <nav>
        <h3>📖 BSG Attendance</h3>
        @if (auth.isAdmin) {
          <a routerLink="/setup" routerLinkActive="active">Setup</a>
        }
        <a routerLink="/members" routerLinkActive="active">Members</a>
        <a routerLink="/visitors" routerLinkActive="active">Visitor Review</a>
        <a routerLink="/test-recognition" routerLinkActive="active">Test Recognition</a>
        <a routerLink="/reports" routerLinkActive="active">Reports</a>
      </nav>
      <div class="content">
        <div class="topbar">
          <span class="muted">Signed in as <b>{{ auth.name() }}</b> ({{ auth.role() }})</span>
          <button class="secondary" (click)="logout()">Log out</button>
        </div>
        <router-outlet></router-outlet>
      </div>
    </div>
  `,
})
export class ShellComponent {
  auth = inject(AuthService);
  private router = inject(Router);
  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
