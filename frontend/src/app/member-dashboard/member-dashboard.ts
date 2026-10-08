import {
  Component,
  OnInit,
  ChangeDetectorRef
} from '@angular/core';

import { Router } from '@angular/router';
import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-member-dashboard',
  imports: [],
  templateUrl: './member-dashboard.html',
  styleUrl: './member-dashboard.css'
})
export class MemberDashboard implements OnInit {

  dashboardData: any = null;

  errorMessage: string = '';

  constructor(
    private dailyWorkService: DailyWorkService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {

    this.loadDashboard();

  }

  loadDashboard(): void {

    this.dailyWorkService.getDashboard().subscribe({

      next: (response) => {

        console.log('Dashboard data:', response);

        this.dashboardData = response;

        this.cdr.detectChanges();

      },

      error: (error) => {

        console.log('Dashboard loading failed');
        console.log(error);

        this.errorMessage = 'Unable to load dashboard data.';

        this.cdr.detectChanges();

      }

    });

  }

  logout(): void {

    this.authService.logout();

    this.router.navigate(['/']);

  }

}