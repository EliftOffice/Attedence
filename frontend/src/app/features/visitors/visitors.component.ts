import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { ApiService, Suggestion, Visitor } from '../../core/api.service';

@Component({
  selector: 'app-visitors',
  standalone: true,
  imports: [FormsModule, DecimalPipe],
  styles: [`
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
    .face { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; background: #edf2f7; }
    .sug { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); }
    .sug-thumb { width: 52px; height: 52px; border-radius: 8px; object-fit: cover; background: #edf2f7; flex: 0 0 auto; }
    .sug-info { flex: 1; min-width: 0; }
    .sug-actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .actions { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
    .new-member { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--border); }
  `],
  template: `
    <h1>Visitor Review</h1>
    <p class="muted">Unmatched faces from your group's meetings. Compare each face against suggested members and resolve it.</p>
    @if (!visitors.length) { <div class="card">No pending visitors 🎉</div> }

    <div class="grid">
      @for (v of visitors; track v.id) {
        <div class="card">
          <img class="face" [src]="cropSrc[v.id] || placeholder" alt="visitor face" />
          <p class="muted">Meeting {{ v.meeting_date }} · #{{ v.id }}</p>

          <button class="secondary" (click)="loadSuggestions(v)">Find matches</button>

          @if (suggestions[v.id]) {
            <div>
              @for (s of suggestions[v.id]; track s.member_id) {
                <div class="sug">
                  <img class="sug-thumb" [src]="sugSrc[s.member_id] || placeholder" alt="{{ s.name }}" />
                  <div class="sug-info">
                    <div>{{ s.name }}
                      <span class="badge">{{ s.same_group ? 'same group' : s.bsg_name }}</span>
                    </div>
                    <span class="muted">match {{ (s.similarity * 100) | number:'1.0-0' }}%</span>
                  </div>
                  <div class="sug-actions">
                    @if (s.same_group) {
                      <button (click)="map(v, s.member_id, false)">Map</button>
                    } @else {
                      <button (click)="map(v, s.member_id, false)" title="mark guest attendance only">Guest</button>
                      <button (click)="map(v, s.member_id, true)" title="move member into this group">Move here</button>
                    }
                  </div>
                </div>
              }
              @if (!suggestions[v.id].length) { <p class="muted">No similar members found.</p> }
            </div>
          }

          <div class="actions">
            <button class="danger" (click)="keep(v)">Keep as visitor</button>
          </div>

          <div class="new-member">
            <label>Register as NEW member (your group)</label>
            <input [(ngModel)]="newName[v.id]" placeholder="Member name" />
            <div class="actions">
              <button (click)="promote(v)" [disabled]="!newName[v.id]">Create &amp; mark present</button>
            </div>
          </div>

          @if (msg[v.id]) { <p class="ok">{{ msg[v.id] }}</p> }
        </div>
      }
    </div>
  `,
})
export class VisitorsComponent implements OnInit {
  private api = inject(ApiService);
  visitors: Visitor[] = [];
  suggestions: Record<number, Suggestion[]> = {};
  cropSrc: Record<number, string> = {};   // visitor id -> object URL
  sugSrc: Record<number, string> = {};    // member id -> object URL
  newName: Record<number, string> = {};
  msg: Record<number, string> = {};
  // 1x1 transparent placeholder
  placeholder = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

  ngOnInit() { this.load(); }

  load() {
    this.api.visitors().subscribe((v) => {
      this.visitors = v;
      // Fetch each visitor crop as an authenticated blob.
      v.forEach((vis) => {
        if (vis.crop_url && !this.cropSrc[vis.id]) {
          this.api.imageObjectUrl(vis.crop_url).subscribe({
            next: (url) => (this.cropSrc[vis.id] = url),
            error: () => {},
          });
        }
      });
    });
  }

  loadSuggestions(v: Visitor) {
    this.api.suggestions(v.id).subscribe((s) => {
      this.suggestions[v.id] = s;
      s.forEach((sug) => {
        if (sug.photo_url && !this.sugSrc[sug.member_id]) {
          this.api.imageObjectUrl(sug.photo_url).subscribe({
            next: (url) => (this.sugSrc[sug.member_id] = url),
            error: () => {},
          });
        }
      });
    });
  }

  private done(v: Visitor, text: string) {
    this.msg[v.id] = text;
    setTimeout(() => this.load(), 700);
  }
  map(v: Visitor, member_id: number, move: boolean) {
    this.api.mapVisitor(v.id, member_id, move).subscribe(() =>
      this.done(v, move ? 'Member moved to your group & marked present.' : 'Marked present.'));
  }
  promote(v: Visitor) {
    this.api.promoteVisitor(v.id, this.newName[v.id]).subscribe(() =>
      this.done(v, 'New member created & marked present.'));
  }
  keep(v: Visitor) {
    this.api.keepVisitor(v.id).subscribe(() => this.done(v, 'Kept as visitor.'));
  }
}
