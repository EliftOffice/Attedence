import { Routes } from '@angular/router';
import { authGuard, adminGuard } from './core/auth.guard';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./features/login/login.component').then((m) => m.LoginComponent) },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shell/shell.component').then((m) => m.ShellComponent),
    children: [
      { path: '', redirectTo: 'visitors', pathMatch: 'full' },
      {
        path: 'setup',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/setup/setup.component').then((m) => m.SetupComponent),
      },
      { path: 'members', loadComponent: () => import('./features/members/members.component').then((m) => m.MembersComponent) },
      { path: 'visitors', loadComponent: () => import('./features/visitors/visitors.component').then((m) => m.VisitorsComponent) },
      { path: 'test-recognition', loadComponent: () => import('./features/test-recognition/test-recognition.component').then((m) => m.TestRecognitionComponent) },
      { path: 'reports', loadComponent: () => import('./features/reports/reports.component').then((m) => m.ReportsComponent) },
    ],
  },
  { path: '**', redirectTo: '' },
];
