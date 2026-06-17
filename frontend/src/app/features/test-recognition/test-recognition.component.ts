import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { AuthService } from '../../core/auth.service';
import { ApiService, Group, RecognitionResult } from '../../core/api.service';

@Component({
  selector: 'app-test-recognition',
  standalone: true,
  imports: [FormsModule, DecimalPipe],
  template: `
    <h1>Test Recognition</h1>
    <p class="muted">Run the same recognition pipeline the Telegram bot uses, on an uploaded photo — no Telegram needed. Validate accuracy before going live.</p>

    <div class="card">
      @if (auth.isAdmin) {
        <div class="field">
          <label>Group</label>
          <select [(ngModel)]="bsgId">
            <option [ngValue]="undefined">— select —</option>
            @for (g of groups; track g.id) { <option [ngValue]="g.id">{{ g.name }}</option> }
          </select>
        </div>
      } @else {
        <div class="field"><label>Group</label><input [value]="'Your group (id ' + (bsgId ?? '?') + ')'" disabled /></div>
      }
      <div class="field"><label>Photo</label><input type="file" accept="image/*" (change)="pick($event)" /></div>
      <label><input type="checkbox" style="width:auto" [(ngModel)]="persist" /> Save attendance &amp; visitors (otherwise dry-run)</label>
      <div style="margin-top:12px">
        <button (click)="run()" [disabled]="!file || !bsgId || loading">{{ loading ? 'Running…' : 'Run recognition' }}</button>
      </div>
      @if (error) { <p class="error">{{ error }}</p> }
    </div>

    @if (result) {
      <div class="card">
        <h2>{{ result.bsg_name }}</h2>
        <p>
          Faces detected: <b>{{ result.faces_detected }}</b> ·
          Recognized: <b>{{ result.recognized_members.length }}</b> ·
          Visitors: <b>{{ result.visitors }}</b> ·
          Discarded: <b>{{ result.discarded.length }}</b> ·
          {{ result.saved ? 'Saved ✅' : 'Dry-run (not saved)' }}
        </p>
        <table>
          <tr><th>Recognized member</th><th>Confidence</th></tr>
          @for (m of result.recognized_members; track m.member_id) {
            <tr><td>{{ m.name }}</td><td>{{ (m.confidence * 100) | number:'1.0-1' }}%</td></tr>
          }
        </table>
        @if (result.discarded.length) {
          <h3>Discarded faces</h3>
          <p class="muted">Thresholds are editable in Setup → ⚙️ Settings. Detector returns faces ≥0.50 score.</p>
          <table>
            <tr><th>Reason</th><th>Det score</th><th>Size px</th><th>Yaw°</th><th>Sharpness</th></tr>
            @for (d of result.discarded; track $index) {
              <tr>
                <td><b>{{ d.reason }}</b></td>
                <td>{{ d.det_score }}</td>
                <td>{{ d.size_px }}</td>
                <td>{{ d.yaw_deg }}</td>
                <td>{{ d.blur_var }}</td>
              </tr>
            }
          </table>
        }
      </div>
    }
  `,
})
export class TestRecognitionComponent implements OnInit {
  auth = inject(AuthService);
  private api = inject(ApiService);
  groups: Group[] = [];
  bsgId?: number;
  file?: File;
  persist = false;
  loading = false;
  error = '';
  result?: RecognitionResult;

  ngOnInit() {
    if (this.auth.isAdmin) {
      this.api.groups().subscribe((g) => (this.groups = g));
    } else {
      this.auth.me().subscribe((m) => (this.bsgId = m.leader_bsg_id ?? undefined));
    }
  }

  pick(ev: Event) {
    const input = ev.target as HTMLInputElement;
    this.file = input.files?.[0];
  }

  run() {
    if (!this.file || !this.bsgId) return;
    this.loading = true; this.error = ''; this.result = undefined;
    this.api.testRecognition(this.bsgId, this.file, this.persist).subscribe({
      next: (r) => { this.loading = false; this.result = r; },
      error: (e) => { this.loading = false; this.error = e?.error?.detail || 'Failed'; },
    });
  }

}
