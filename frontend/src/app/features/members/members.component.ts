import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth.service';
import { ApiService, City, DirectoryRow, Group, Member, Street } from '../../core/api.service';

@Component({
  selector: 'app-members',
  standalone: true,
  imports: [FormsModule],
  styles: [`
    .inactive td { opacity: 0.55; }
    .badge.active { background: #c6f6d5; color: #22543d; }
    .badge.inactive { background: #fed7d7; color: #742a2a; }
    .edit-panel { border: 2px solid var(--primary); }
  `],
  template: `
    <h1>Members &amp; Facial Profiles</h1>

    @if (auth.isAdmin) {
      <div class="card">
        <label>Group</label>
        <select [(ngModel)]="bsgId" (ngModelChange)="load()">
          <option [ngValue]="undefined">— select a group —</option>
          @for (g of groups; track g.id) { <option [ngValue]="g.id">{{ g.name }}</option> }
        </select>
      </div>
    }

    <div class="card">
      <h2>Register member</h2>
      <p class="muted">Only <b>Name</b> is required — everything else is optional.</p>
      <div class="row">
        <div class="field"><label>Name *</label><input [(ngModel)]="name" /></div>
        <div class="field"><label>Surname</label><input [(ngModel)]="surname" /></div>
        <div class="field"><label>Mobile</label><input [(ngModel)]="mobile" /></div>
      </div>
      <div class="row">
        <div class="field">
          <label>City</label>
          <select [(ngModel)]="cityId" (ngModelChange)="onCityChange()">
            <option [ngValue]="undefined">—</option>
            @for (c of cities; track c.id) { <option [ngValue]="c.id">{{ c.name }}</option> }
          </select>
        </div>
        <div class="field">
          <label>Street</label>
          <select [(ngModel)]="streetId" [disabled]="!cityId">
            <option [ngValue]="undefined">—</option>
            @for (s of streets; track s.id) { <option [ngValue]="s.id">{{ s.name }}</option> }
          </select>
        </div>
      </div>
      <button (click)="add()" [disabled]="!name || (auth.isAdmin && !bsgId)">Add member</button>
      @if (error) { <p class="error">{{ error }}</p> }
    </div>

    @if (editId) {
      <div class="card edit-panel">
        <h2>Edit member</h2>
        <div class="row">
          <div class="field"><label>Name *</label><input [(ngModel)]="eName" /></div>
          <div class="field"><label>Surname</label><input [(ngModel)]="eSurname" /></div>
          <div class="field"><label>Mobile</label><input [(ngModel)]="eMobile" /></div>
        </div>
        <div class="row">
          <div class="field">
            <label>City</label>
            <select [(ngModel)]="eCityId" (ngModelChange)="onEditCityChange()">
              <option [ngValue]="undefined">—</option>
              @for (c of cities; track c.id) { <option [ngValue]="c.id">{{ c.name }}</option> }
            </select>
          </div>
          <div class="field">
            <label>Street</label>
            <select [(ngModel)]="eStreetId" [disabled]="!eCityId">
              <option [ngValue]="undefined">—</option>
              @for (s of eStreets; track s.id) { <option [ngValue]="s.id">{{ s.name }}</option> }
            </select>
          </div>
          <div class="field">
            <label>Status</label>
            <select [(ngModel)]="eStatus">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </div>
        </div>
        <button (click)="saveEdit()" [disabled]="!eName">Save</button>
        <button class="secondary" (click)="editId = undefined">Cancel</button>
      </div>
    }

    <div class="card">
      <h2>Members</h2>
      <table>
        <tr><th>Name</th><th>Mobile</th><th>Address</th><th>Status</th><th>Photos</th><th>Add photos</th><th>Actions</th></tr>
        @for (m of members; track m.id) {
          <tr [class.inactive]="m.status === 'inactive'">
            <td>{{ m.name }} {{ m.surname }}</td>
            <td>{{ m.mobile_number }}</td>
            <td class="muted">{{ m.street_name }}{{ m.street_name && m.city_name ? ', ' : '' }}{{ m.city_name }}</td>
            <td><span class="badge" [class]="m.status">{{ m.status }}</span></td>
            <td><span class="badge">{{ m.photo_count }}</span></td>
            <td>
              <input type="file" multiple accept="image/*" (change)="upload(m, $event)" />
              @if (uploadingId === m.id) { <span class="muted">uploading…</span> }
            </td>
            <td>
              <button class="secondary" (click)="beginEdit(m)">Edit</button>
              <button class="secondary" (click)="toggleStatus(m)">
                {{ m.status === 'active' ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
        }
      </table>
      @if (uploadMsg) { <p [class]="uploadOk ? 'ok' : 'error'">{{ uploadMsg }}</p> }
    </div>

    <div class="card">
      <h2>Pull a member from another group</h2>
      <p class="muted">Transfer an existing member from another BSG into {{ auth.isAdmin ? 'a' : 'your' }} group.
        Their facial profile moves with them; attendance history stays where it was.</p>
      <div class="row">
        <div class="field"><label>Search by name/surname</label><input [(ngModel)]="search" (keyup.enter)="runSearch()" /></div>
        @if (auth.isAdmin) {
          <div class="field">
            <label>Pull into group</label>
            <select [(ngModel)]="targetBsgId">
              <option [ngValue]="undefined">— select —</option>
              @for (g of groups; track g.id) { <option [ngValue]="g.id">{{ g.name }}</option> }
            </select>
          </div>
        }
      </div>
      <button class="secondary" (click)="runSearch()">Search</button>
      <table>
        <tr><th>Name</th><th>Current group</th><th></th></tr>
        @for (d of directory; track d.id) {
          <tr>
            <td>{{ d.name }} {{ d.surname }}</td>
            <td>{{ d.bsg_name }}</td>
            <td><button (click)="pull(d)" [disabled]="auth.isAdmin && !targetBsgId">Pull here</button></td>
          </tr>
        }
      </table>
      @if (transferMsg) { <p class="ok">{{ transferMsg }}</p> }
    </div>
  `,
})
export class MembersComponent implements OnInit {
  auth = inject(AuthService);
  private api = inject(ApiService);
  groups: Group[] = [];
  members: Member[] = [];
  cities: City[] = [];
  streets: Street[] = [];
  bsgId?: number;
  name = ''; surname = ''; mobile = ''; cityId?: number; streetId?: number;
  error = ''; uploadMsg = ''; uploadOk = false; uploadingId?: number;
  // edit
  editId?: number;
  eName = ''; eSurname = ''; eMobile = ''; eCityId?: number; eStreetId?: number; eStatus = 'active';
  eStreets: Street[] = [];
  // transfer / pull
  search = ''; directory: DirectoryRow[] = []; targetBsgId?: number; transferMsg = '';

  ngOnInit() {
    this.api.cities().subscribe((c) => (this.cities = c));
    if (this.auth.isAdmin) {
      this.api.groups().subscribe((g) => (this.groups = g));
    } else {
      this.load();
    }
  }

  load() { this.api.members(this.bsgId).subscribe((m) => (this.members = m)); }

  onCityChange() {
    this.streetId = undefined; this.streets = [];
    if (this.cityId) this.api.streets(this.cityId).subscribe((s) => (this.streets = s));
  }

  add() {
    this.error = '';
    this.api.createMember({
      name: this.name, surname: this.surname || undefined, mobile_number: this.mobile || undefined,
      city_id: this.cityId, street_id: this.streetId, bsg_id: this.bsgId,
    }).subscribe({
      next: () => {
        this.name = this.surname = this.mobile = '';
        this.cityId = this.streetId = undefined; this.streets = [];
        this.load();
      },
      error: (e) => (this.error = e?.error?.detail || 'Failed'),
    });
  }

  beginEdit(m: Member) {
    this.editId = m.id;
    this.eName = m.name; this.eSurname = m.surname || ''; this.eMobile = m.mobile_number || '';
    this.eCityId = m.city_id || undefined; this.eStreetId = m.street_id || undefined;
    this.eStatus = m.status; this.eStreets = [];
    if (this.eCityId) this.api.streets(this.eCityId).subscribe((s) => (this.eStreets = s));
  }
  onEditCityChange() {
    this.eStreetId = undefined; this.eStreets = [];
    if (this.eCityId) this.api.streets(this.eCityId).subscribe((s) => (this.eStreets = s));
  }
  saveEdit() {
    if (!this.editId) return;
    this.api.updateMember(this.editId, {
      name: this.eName, surname: this.eSurname, mobile_number: this.eMobile,
      city_id: this.eCityId, street_id: this.eStreetId, status: this.eStatus,
    }).subscribe(() => { this.editId = undefined; this.load(); });
  }
  toggleStatus(m: Member) {
    this.api.updateMember(m.id, { status: m.status === 'active' ? 'inactive' : 'active' })
      .subscribe(() => this.load());
  }

  upload(m: Member, ev: Event) {
    const input = ev.target as HTMLInputElement;
    if (!input.files?.length) return;
    const files = Array.from(input.files);
    this.uploadingId = m.id; this.uploadMsg = '';
    this.api.addPhotos(m.id, files).subscribe({
      next: () => {
        this.uploadingId = undefined; this.uploadOk = true;
        this.uploadMsg = `Added ${files.length} photo(s) to ${m.name}'s profile.`;
        input.value = ''; this.load();
      },
      error: (e) => {
        this.uploadingId = undefined; this.uploadOk = false;
        this.uploadMsg = e?.error?.detail?.message || e?.error?.detail || 'Upload failed (no clear face?)';
      },
    });
  }

  runSearch() {
    this.api.directory(this.search || undefined).subscribe((d) => (this.directory = d));
  }
  pull(d: DirectoryRow) {
    this.transferMsg = '';
    this.api.transferMember(d.id, this.auth.isAdmin ? this.targetBsgId : undefined).subscribe({
      next: () => { this.transferMsg = `${d.name} pulled in successfully.`; this.runSearch(); this.load(); },
      error: (e) => (this.transferMsg = e?.error?.detail || 'Transfer failed'),
    });
  }
}
