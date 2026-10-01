import { Routes } from '@angular/router';

import { Login } from './login/login';
import { MemberDashboard } from './member-dashboard/member-dashboard';
import { TeamAdminDashboard } from './team-admin-dashboard/team-admin-dashboard';
import { SuperAdminDashboard } from './super-admin-dashboard/super-admin-dashboard';
import { authGuard } from './guards/auth-guard';

export const routes: Routes = [

  {
    path: '',
    component: Login
  },

  {
    path: 'member-dashboard',
    component: MemberDashboard,
    canActivate: [authGuard]
  },

  {
    path: 'team-admin-dashboard',
    component: TeamAdminDashboard,
    canActivate: [authGuard]
  },

  {
    path: 'super-admin-dashboard',
    component: SuperAdminDashboard,
    canActivate: [authGuard]
  }

];