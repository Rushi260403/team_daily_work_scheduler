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
    canActivate: [authGuard],
    data: {
      role: 'MEMBER'
    }
  },

  {
    path: 'team-admin-dashboard',
    component: TeamAdminDashboard,
    canActivate: [authGuard],
    data: {
      role: 'TEAM_ADMIN'
    }
  },

  {
    path: 'super-admin-dashboard',
    component: SuperAdminDashboard,
    canActivate: [authGuard],
    data: {
      role: 'SUPER_ADMIN'
    }
  }

];