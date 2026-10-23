
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-team-admin-dashboard',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './team-admin-dashboard.html',
  styleUrl: './team-admin-dashboard.css',
})
export class TeamAdminDashboard implements OnInit {
  user: any = null;

  summary = {
    total_work_days: 0,
    completed_days: 0,
    pending_days: 0,
    latest_work_date: null as string | null,
  };

  workHistory: any[] = [];
  historySearch = '';
  historyStartDate = '';
  historyEndDate = '';

  dashboardLoading = false;
  historyLoading = false;
  dashboardError = '';
  historyError = '';

  constructor(
    private dailyWorkService: DailyWorkService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.loadWorkHistory();
  }

  loadDashboard(): void {
    this.dashboardLoading = true;
    this.dashboardError = '';

    this.dailyWorkService.getDashboard().subscribe({
      next: (response: any) => {
        this.user = response.user ?? null;
        this.summary = {
          total_work_days: response.summary?.total_work_days ?? 0,
          completed_days: response.summary?.completed_days ?? 0,
          pending_days: response.summary?.pending_days ?? 0,
          latest_work_date: response.summary?.latest_work_date ?? null,
        };

        this.dashboardLoading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Dashboard loading failed:', error);
        this.dashboardError = 'Unable to load dashboard information.';
        this.dashboardLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  loadWorkHistory(): void {
    this.historyLoading = true;
    this.historyError = '';

    this.dailyWorkService.getTeamWorkHistory().subscribe({
      next: (response: any) => {
        this.workHistory = response.work ?? [];
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Team work history loading failed:', error);
        this.historyError = 'Unable to load team work history.';
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  get filteredWorkHistory(): any[] {
    const search = this.historySearch.trim().toLowerCase();

    return this.workHistory.filter((record: any) => {
      const recordDate = record.work_date ?? '';

      const matchesStartDate =
        !this.historyStartDate || recordDate >= this.historyStartDate;

      const matchesEndDate =
        !this.historyEndDate || recordDate <= this.historyEndDate;

      const searchableText = [
        record.user_name,
        record.user_email,
        record.team_name,
        record.work_date,
        record.office_in_time,
        record.working_points,
        record.office_out_time,
        record.points_completed,
        record.pending_points,
      ]
        .filter((value: any) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();

      return (
        matchesStartDate &&
        matchesEndDate &&
        (!search || searchableText.includes(search))
      );
    });
  }

  clearHistoryFilters(): void {
    this.historySearch = '';
    this.historyStartDate = '';
    this.historyEndDate = '';
  }

  refreshWorkHistory(): void {
    this.loadWorkHistory();
  }

  logout(): void {
    this.authService.logout();
  }
}
