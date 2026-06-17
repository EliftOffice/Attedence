import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  styles: [`
    .wrap { display: grid; place-items: center; min-height: 100vh; }
    .box { width: 340px; }
    h1 { text-align: center; }
  `],
  template: `
    <div class="wrap">
      <div class="card box">
        <h1>📖 BSG Attendance</h1>
        <div class="field">
          <label>Mobile number</label>
          <input [(ngModel)]="mobile" placeholder="+91..." autocomplete="username" />
        </div>
        <div class="field">
          <label>Password</label>
          <input type="password" [(ngModel)]="password" (keyup.enter)="submit()" autocomplete="current-password" />
        </div>
        @if (error) { <p class="error">{{ error }}</p> }
        <button (click)="submit()" [disabled]="loading" style="width:100%">
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </div>
    </div>
  `,
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);
  mobile = '';
  password = '';
  loading = false;
  error = '';

  submit() {
    this.error = '';
    this.loading = true;
    this.auth.login(this.mobile, this.password).subscribe({
      next: () => { this.loading = false; this.router.navigate(['/']); },
      error: (e) => { this.loading = false; this.error = e?.error?.detail || 'Login failed'; },
    });
  }
}
