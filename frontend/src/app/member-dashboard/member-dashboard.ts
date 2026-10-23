import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-member-dashboard',
  imports: [FormsModule],
  templateUrl: './member-dashboard.html',
  styleUrl: './member-dashboard.css',
})
export class MemberDashboard implements OnInit {
  private morningMessageTimer?: ReturnType<typeof setTimeout>;
  private eveningMessageTimer?: ReturnType<typeof setTimeout>;
  private errorMessageTimer?: ReturnType<typeof setTimeout>;
  private eveningErrorMessageTimer?: ReturnType<typeof setTimeout>;
  private historicalRequestMessageTimer?: ReturnType<typeof setTimeout>;
  private historicalRequestErrorTimer?: ReturnType<typeof setTimeout>;
  dashboardData: any = null;

  morningSubmitting: boolean = false;
  eveningSubmitting: boolean = false;

  errorMessage: string = '';

  // Morning Work fields
  workDate: string = '';
  officeInTime: string = '';
  workingPoints: string = '';
  morningMessage: string = '';

  // Evening Work fields
  officeOutTime: string = '';
  pointsCompleted: string = '';
  pendingPoints: string = '';
  eveningMessage: string = '';
  eveningErrorMessage: string = '';

  // Historical Edit Request fields
  historicalEditReason: string = '';
  historicalRequestSubmitting: boolean = false;
  historicalRequestMessage: string = '';
  historicalRequestError: string = '';

  workHistory: any[] = [];
  selectedHistoricalWorkDate = '';
  historyLoading = false;
  historyError = '';
  historySearch = '';
  historyStartDate = '';
  historyEndDate = '';

  constructor(
    private dailyWorkService: DailyWorkService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.setTodayDate();
    this.loadDashboard();
    this.loadWorkHistory();
  }

  setTodayDate(): void {
    const today = new Date();
    this.workDate = today.toISOString().split('T')[0];
  }

  loadDashboard(): void {
    this.dailyWorkService.getDashboard().subscribe({
      next: (response) => {
        console.log('Dashboard data:', response);
        this.dashboardData = response;
        this.cdr.detectChanges();
      },

      error: (error) => {
        console.log('Dashboard loading failed:', error);
        this.errorMessage = 'Unable to load dashboard data.';
        this.cdr.detectChanges();
      },
    });
  }

  submitMorningWork(): void {
    // Prevent repeated clicks while submitting
    if (this.morningSubmitting) {
      return;
    }

    this.morningMessage = '';
    this.errorMessage = '';

    // Validate required fields
    if (!this.workDate || !this.officeInTime || !this.workingPoints.trim()) {
      this.errorMessage = 'Please fill all morning work fields.';
      return;
    }

    this.morningSubmitting = true;

    this.dailyWorkService
      .submitMorningWork(this.workDate, this.officeInTime, this.workingPoints)
      .subscribe({
        next: (response) => {
          console.log('Morning work submitted:', response);

          this.showMorningMessage('Morning work submitted successfully.');
          this.morningSubmitting = false;

          this.loadWorkHistory();
          this.loadDashboard();
          this.cdr.detectChanges();
        },

        error: (error) => {
          console.log('Morning work submission failed:', error);

          this.showErrorMessage(error.error?.detail || 'Unable to submit morning work.');

          this.morningSubmitting = false;
          this.cdr.detectChanges();
        },
      });
  }

  submitEveningWork(): void {
    // Prevent repeated clicks while submitting
    if (this.eveningSubmitting) {
      return;
    }

    this.eveningMessage = '';
    this.eveningErrorMessage = '';
    this.errorMessage = '';

    // Pending Points is optional
    if (!this.workDate || !this.officeOutTime || !this.pointsCompleted.trim()) {
      this.eveningErrorMessage = 'Please fill Work Date, Office Out Time, and Points Completed.';
      return;
    }

    this.eveningSubmitting = true;

    this.dailyWorkService
      .submitEveningWork(
        this.workDate,
        this.officeOutTime,
        this.pointsCompleted,
        this.pendingPoints.trim(),
      )
      .subscribe({
        next: (response) => {
          console.log('Evening work submitted:', response);

          this.showEveningMessage('Evening work submitted successfully.');
          this.eveningSubmitting = false;
          this.loadWorkHistory();
          this.loadDashboard();
          this.cdr.detectChanges();
        },

        error: (error) => {
          console.log('Evening work submission failed:', error);

          this.showEveningErrorMessage(error.error?.detail || 'Unable to submit evening work.');

          this.eveningSubmitting = false;
          this.cdr.detectChanges();
        },
      });
  }

  private showMorningMessage(message: string): void {
    this.morningMessage = message;

    clearTimeout(this.morningMessageTimer);

    this.morningMessageTimer = setTimeout(() => {
      this.morningMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  private showEveningMessage(message: string): void {
    this.eveningMessage = message;

    clearTimeout(this.eveningMessageTimer);

    this.eveningMessageTimer = setTimeout(() => {
      this.eveningMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  private showErrorMessage(message: string): void {
    this.errorMessage = message;

    clearTimeout(this.errorMessageTimer);

    this.errorMessageTimer = setTimeout(() => {
      this.errorMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  private showEveningErrorMessage(message: string): void {
    this.eveningErrorMessage = message;

    clearTimeout(this.eveningErrorMessageTimer);

    this.eveningErrorMessageTimer = setTimeout(() => {
      this.eveningErrorMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/']);
  }

  submitHistoricalEditRequest(): void {
    this.historicalRequestMessage = '';
    this.historicalRequestError = '';

    if (this.historicalRequestSubmitting) {
      return;
    }

    if (!this.selectedHistoricalWorkDate || !this.historicalEditReason.trim()) {
      this.historicalRequestError = 'Please select a work date and enter a reason.';
      return;
    }

    if (this.historicalEditReason.trim().length < 5) {
      this.historicalRequestError = 'The reason must contain at least 5 characters.';
      return;
    }

    // Find the selected record using its work date.
    const selectedRecord = this.workHistory.find(
      (record: any) => record.work_date === this.selectedHistoricalWorkDate,
    );

    if (!selectedRecord) {
      this.historicalRequestError =
        'Selected work record was not found. Please reload your history.';
      return;
    }

    // Use the internal ID without displaying it in the form.
    const dailyWorkId = selectedRecord.id;

    this.historicalRequestSubmitting = true;

    this.dailyWorkService
      .requestHistoricalEdit(dailyWorkId, this.historicalEditReason.trim())
      .subscribe({
        next: (response) => {
          this.historicalRequestMessage =
            response?.message || 'Historical edit request submitted successfully.';

          this.historicalRequestError = '';
          this.selectedHistoricalWorkDate = '';
          this.historicalEditReason = '';
          this.historicalRequestSubmitting = false;

          clearTimeout(this.historicalRequestMessageTimer);

          this.historicalRequestMessageTimer = setTimeout(() => {
            this.historicalRequestMessage = '';
            this.cdr.detectChanges();
          }, 5000);

          this.cdr.detectChanges();
        },

        error: (error) => {
          this.historicalRequestError =
            error.error?.detail || 'Unable to submit the historical edit request.';

          this.historicalRequestMessage = '';
          this.historicalRequestSubmitting = false;

          clearTimeout(this.historicalRequestErrorTimer);

          this.historicalRequestErrorTimer = setTimeout(() => {
            this.historicalRequestError = '';
            this.cdr.detectChanges();
          }, 5000);

          this.cdr.detectChanges();
        },
      });
  }

  loadWorkHistory(): void {
    this.historyLoading = true;
    this.historyError = '';

    this.dailyWorkService.getMyWorkHistory().subscribe({
      next: (response: any) => {
        this.workHistory = response.daily_work ?? [];
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Work history loading failed:', error);
        this.historyError = 'Unable to load work history.';
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  get filteredWorkHistory(): any[] {
    const search = this.historySearch.trim().toLowerCase();

    return this.workHistory.filter((record: any) => {
      const recordDate = String(record.work_date ?? '').slice(0, 10);

      // Filter by start date
      if (this.historyStartDate && recordDate < this.historyStartDate) {
        return false;
      }

      // Filter by end date
      if (this.historyEndDate && recordDate > this.historyEndDate) {
        return false;
      }

      // Search across record details
      if (search) {
        const searchableText = [
          record.work_date,
          record.office_in_time,
          record.working_points,
          record.office_out_time,
          record.points_completed,
          record.pending_points,
        ]
          .join(' ')
          .toLowerCase();

        if (!searchableText.includes(search)) {
          return false;
        }
      }

      return true;
    });
  }
  clearHistoryFilters(): void {
    this.historySearch = '';
    this.historyStartDate = '';
    this.historyEndDate = '';
  }
}
