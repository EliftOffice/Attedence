import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, AppSettings, Church, City, Group, Leader, Street } from '../../core/api.service';

@Component({
  selector: 'app-setup',
  standalone: true,
  imports: [FormsModule],
  template: `
    <h1>Setup &amp; Management</h1>

    <div class="row">
      <div class="card">
        <h2>Churches</h2>
        <div class="field"><input [(ngModel)]="newChurch" placeholder="Church name" /></div>
        <button (click)="addChurch()" [disabled]="!newChurch">Add church</button>
        <table>
          <tr><th>ID</th><th>Name</th></tr>
          @for (c of churches; track c.id) { <tr><td>{{ c.id }}</td><td>{{ c.name }}</td></tr> }
        </table>
      </div>

      <div class="card">
        <h2>Groups (BSG)</h2>
        <div class="field">
          <label>Church</label>
          <select [(ngModel)]="groupChurchId">
            @for (c of churches; track c.id) { <option [value]="c.id">{{ c.name }}</option> }
          </select>
        </div>
        <div class="field"><input [(ngModel)]="newGroup" placeholder="Group name" /></div>
        <div class="field"><input [(ngModel)]="newGroupDay" placeholder="Meeting day (optional)" /></div>
        <button (click)="addGroup()" [disabled]="!newGroup || !groupChurchId">Add group</button>
        <table>
          <tr><th>ID</th><th>Name</th><th>Day</th></tr>
          @for (g of groups; track g.id) { <tr><td>{{ g.id }}</td><td>{{ g.name }}</td><td>{{ g.meeting_day }}</td></tr> }
        </table>
      </div>
    </div>

    @if (settings) {
      <div class="card">
        <h2>⚙️ Settings (Telegram &amp; recognition)</h2>
        <p class="muted">Editable here so they can be changed without redeploying. The bot
          picks up a new token automatically (it restarts itself within ~30s).</p>
        <div class="row">
          <div class="field">
            <label>Telegram bot token {{ settings.telegram_token_set ? '(currently ' + settings.telegram_bot_token + ')' : '(not set)' }}</label>
            <input [(ngModel)]="tgToken" placeholder="paste new token to change; leave blank to keep" />
          </div>
          <div class="field">
            <label>Match sender on</label>
            <select [(ngModel)]="settings.telegram_match_field">
              <option value="user_id">user_id (default)</option>
              <option value="chat_id">chat_id</option>
            </select>
          </div>
          <div class="field">
            <label>Group reply</label>
            <select [(ngModel)]="settings.telegram_reply_mode">
              <option value="minimal">minimal</option>
              <option value="silent">silent</option>
              <option value="private">private</option>
            </select>
          </div>
        </div>
        <div class="row">
          <div class="field"><label>Match threshold</label><input type="number" step="0.01" [(ngModel)]="settings.face_match_threshold" /></div>
          <div class="field"><label>Min detector score</label><input type="number" step="0.01" [(ngModel)]="settings.face_det_score_min" /></div>
          <div class="field"><label>Min face px</label><input type="number" [(ngModel)]="settings.face_min_pixels" /></div>
          <div class="field"><label>Max yaw°</label><input type="number" [(ngModel)]="settings.face_max_yaw_deg" /></div>
          <div class="field"><label>Min sharpness</label><input type="number" step="1" [(ngModel)]="settings.face_blur_var_min" /></div>
        </div>
        <label><input type="checkbox" style="width:auto" [(ngModel)]="settings.discard_low_quality" />
          Discard low-quality faces (off = send them to Visitors for manual marking)</label>
        <div style="margin-top:10px"><button (click)="saveSettings()">Save settings</button></div>
        @if (settingsMsg) { <span class="ok" style="margin-left:10px">{{ settingsMsg }}</span> }
      </div>
    }

    <div class="row">
      <div class="card">
        <h2>Cities</h2>
        <p class="muted">Admin-managed dropdown values for member addresses.</p>
        <div class="field"><input [(ngModel)]="newCity" placeholder="City name" /></div>
        <button (click)="addCity()" [disabled]="!newCity">Add city</button>
        <table>
          <tr><th>ID</th><th>Name</th></tr>
          @for (c of cities; track c.id) { <tr><td>{{ c.id }}</td><td>{{ c.name }}</td></tr> }
        </table>
      </div>

      <div class="card">
        <h2>Streets</h2>
        <div class="field">
          <label>City</label>
          <select [(ngModel)]="streetCityId" (ngModelChange)="loadStreets()">
            <option [ngValue]="undefined">— select city —</option>
            @for (c of cities; track c.id) { <option [ngValue]="c.id">{{ c.name }}</option> }
          </select>
        </div>
        <div class="field"><input [(ngModel)]="newStreet" placeholder="Street name" /></div>
        <button (click)="addStreet()" [disabled]="!newStreet || !streetCityId">Add street</button>
        <table>
          <tr><th>ID</th><th>Street</th></tr>
          @for (s of streets; track s.id) { <tr><td>{{ s.id }}</td><td>{{ s.name }}</td></tr> }
        </table>
      </div>
    </div>

    <div class="card">
      <h2>Leaders</h2>
      <p class="muted">Creating a leader makes their login (mobile + password) and assigns one group.
        To replace a leader: <b>Deactivate</b> the current one (frees the group), then add the new leader on that group.</p>
      <div class="row">
        <div class="field">
          <label>Group</label>
          <select [(ngModel)]="leaderGroupId">
            @for (g of groups; track g.id) { <option [value]="g.id">{{ g.name }}</option> }
          </select>
        </div>
        <div class="field"><label>Name</label><input [(ngModel)]="leaderName" /></div>
        <div class="field"><label>Mobile</label><input [(ngModel)]="leaderMobile" /></div>
        <div class="field"><label>Password</label><input type="password" [(ngModel)]="leaderPwd" /></div>
      </div>
      <button (click)="addLeader()" [disabled]="!leaderGroupId || !leaderName || !leaderMobile || !leaderPwd">Add leader</button>
      @if (error) { <p class="error">{{ error }}</p> }
      <table>
        <tr><th>ID</th><th>Name</th><th>Group</th><th>Telegram</th><th>Actions</th></tr>
        @for (l of leaders; track l.id) {
          <tr>
            <td>{{ l.id }}</td><td>{{ l.name }}</td><td>{{ groupName(l.bsg_id) }}</td>
            <td>{{ l.telegram_user_id ? '✅ linked' : '— not linked' }}</td>
            <td>
              <button class="secondary" (click)="getCode(l)">Get link code</button>
              <button class="danger" (click)="deactivate(l)">Deactivate</button>
            </td>
          </tr>
          @if (codeFor === l.id && code) {
            <tr><td colspan="5"><pre class="ok">{{ code }}</pre></td></tr>
          }
        }
      </table>
    </div>
  `,
})
export class SetupComponent implements OnInit {
  private api = inject(ApiService);
  churches: Church[] = [];
  groups: Group[] = [];
  leaders: Leader[] = [];
  cities: City[] = [];
  streets: Street[] = [];
  newChurch = ''; newGroup = ''; newGroupDay = '';
  newCity = ''; newStreet = ''; streetCityId?: number;
  groupChurchId?: number; leaderGroupId?: number;
  leaderName = ''; leaderMobile = ''; leaderPwd = '';
  error = ''; code = ''; codeFor?: number;
  settings?: AppSettings; tgToken = ''; settingsMsg = '';

  ngOnInit() { this.reload(); }

  reload() {
    this.api.churches().subscribe((c) => (this.churches = c));
    this.api.groups().subscribe((g) => (this.groups = g));
    this.api.leaders().subscribe((l) => (this.leaders = l));
    this.api.cities().subscribe((c) => (this.cities = c));
    this.api.getSettings().subscribe((s) => (this.settings = s));
  }
  saveSettings() {
    if (!this.settings) return;
    const body: any = {
      telegram_match_field: this.settings.telegram_match_field,
      telegram_reply_mode: this.settings.telegram_reply_mode,
      face_match_threshold: this.settings.face_match_threshold,
      face_det_score_min: this.settings.face_det_score_min,
      face_min_pixels: this.settings.face_min_pixels,
      face_max_yaw_deg: this.settings.face_max_yaw_deg,
      face_blur_var_min: this.settings.face_blur_var_min,
      discard_low_quality: this.settings.discard_low_quality,
    };
    if (this.tgToken.trim()) body.telegram_bot_token = this.tgToken.trim();
    this.api.updateSettings(body).subscribe((s) => {
      this.settings = s; this.tgToken = ''; this.settingsMsg = 'Saved ✓';
      setTimeout(() => (this.settingsMsg = ''), 2500);
    });
  }
  loadStreets() {
    if (this.streetCityId) this.api.streets(this.streetCityId).subscribe((s) => (this.streets = s));
    else this.streets = [];
  }
  addCity() { this.api.createCity(this.newCity).subscribe(() => { this.newCity = ''; this.reload(); }); }
  addStreet() {
    this.api.createStreet(+this.streetCityId!, this.newStreet).subscribe(() => { this.newStreet = ''; this.loadStreets(); });
  }
  addChurch() { this.api.createChurch(this.newChurch).subscribe(() => { this.newChurch = ''; this.reload(); }); }
  addGroup() {
    this.api.createGroup({ church_id: +this.groupChurchId!, name: this.newGroup, meeting_day: this.newGroupDay || undefined })
      .subscribe(() => { this.newGroup = ''; this.newGroupDay = ''; this.reload(); });
  }
  addLeader() {
    this.error = '';
    this.api.createLeader({ bsg_id: +this.leaderGroupId!, name: this.leaderName, mobile_number: this.leaderMobile, password: this.leaderPwd })
      .subscribe({
        next: () => { this.leaderName = this.leaderMobile = this.leaderPwd = ''; this.reload(); },
        error: (e) => (this.error = e?.error?.detail || 'Failed'),
      });
  }
  getCode(l: Leader) {
    this.api.leaderLinkCode(l.id).subscribe((r) => { this.code = r.instructions; this.codeFor = l.id; });
  }
  groupName(bsg_id: number) {
    return this.groups.find((g) => g.id === bsg_id)?.name ?? bsg_id;
  }
  deactivate(l: Leader) {
    if (!confirm(`Deactivate ${l.name}? Their login is disabled and the group is freed for a new leader.`)) return;
    this.api.deactivateLeader(l.id).subscribe(() => this.reload());
  }
}
