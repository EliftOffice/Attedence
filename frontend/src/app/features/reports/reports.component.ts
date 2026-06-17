import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { AuthService } from '../../core/auth.service';
import { ApiService, Group } from '../../core/api.service';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [FormsModule, DecimalPipe],
  template: `
    <h1>Reports</h1>

    @if (auth.isAdmin) {
      <div class="card">
        <label>Group</label>
        <select [(ngModel)]="bsgId" (ngModelChange)="load()">
          <option [ngValue]="undefined">— select —</option>
          @for (g of groups; track g.id) { <option [ngValue]="g.id">{{ g.name }}</option> }
        </select>
      </div>
    }

    @if (stats) {
      <div class="card">
        <h2>Visitor statistics</h2>
        <p>Total: <b>{{ stats.total_visitor_entries }}</b> · Pending: <b>{{ stats.pending }}</b> ·
           Kept: <b>{{ stats.kept }}</b> · Promoted: <b>{{ stats.promoted }}</b> · Mapped: <b>{{ stats.mapped }}</b></p>
      </div>
    }

    <div class="card">
      <h2>Member attendance %</h2>
      <table>
        <tr><th>Member</th><th>Attended</th><th>Held</th><th>%</th></tr>
        @for (r of memberAtt; track r.member_id) {
          <tr><td>{{ r.name }}</td><td>{{ r.meetings_attended }}</td><td>{{ r.meetings_held }}</td>
              <td>{{ r.attendance_pct | number:'1.0-1' }}%</td></tr>
        }
      </table>
    </div>

    <div class="card">
      <h2>Attendance by meeting</h2>
      <table>
        <tr><th>Date</th><th>Present</th><th>Guests</th></tr>
        @for (r of groupAtt; track r.meeting_id) {
          <tr><td>{{ r.meeting_date }}</td><td>{{ r.present }}</td><td>{{ r.guests }}</td></tr>
        }
      </table>
    </div>

    <div class="row">
      <div class="card">
        <h2>Growth (cumulative)</h2>
        <table>
          <tr><th>Month</th><th>Members</th></tr>
          @for (r of growth; track r.period) { <tr><td>{{ r.period }}</td><td>{{ r.members }}</td></tr> }
        </table>
      </div>
      <div class="card">
        <h2>Long-term absentees</h2>
        <table>
          <tr><th>Member</th><th>Last attended</th><th>Missed in a row</th></tr>
          @for (r of absentees; track r.member_id) {
            <tr><td>{{ r.name }}</td><td>{{ r.last_attended || '—' }}</td><td>{{ r.meetings_missed_in_row }}</td></tr>
          }
        </table>
      </div>
    </div>
  `,
})
export class ReportsComponent implements OnInit {
  auth = inject(AuthService);
  private api = inject(ApiService);
  groups: Group[] = [];
  bsgId?: number;
  stats: any; memberAtt: any[] = []; groupAtt: any[] = []; growth: any[] = []; absentees: any[] = [];

  ngOnInit() {
    if (this.auth.isAdmin) {
      this.api.groups().subscribe((g) => (this.groups = g));
    } else {
      this.load();
    }
  }

  load() {
    if (this.auth.isAdmin && !this.bsgId) return;
    this.api.visitorStats(this.bsgId).subscribe((s) => (this.stats = s));
    this.api.memberAttendance(this.bsgId).subscribe((r) => (this.memberAtt = r));
    this.api.groupAttendance(this.bsgId).subscribe((r) => (this.groupAtt = r));
    this.api.growth(this.bsgId).subscribe((r) => (this.growth = r));
    this.api.absentees(this.bsgId).subscribe((r) => (this.absentees = r));
  }
}
