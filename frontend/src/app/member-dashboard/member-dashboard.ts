import { Component, OnInit, ChangeDetectorRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-member-dashboard',
  imports: [CommonModule, FormsModule],
  templateUrl: './member-dashboard.html',
  styleUrl: './member-dashboard.css',
})
export class MemberDashboard implements OnInit, OnDestroy {
  // Separate timers for each message
  private morningMessageTimer?: ReturnType<typeof setTimeout>;
  private eveningMessageTimer?: ReturnType<typeof setTimeout>;
  private errorMessageTimer?: ReturnType<typeof setTimeout>;
  private eveningErrorMessageTimer?: ReturnType<typeof setTimeout>;
  private historicalRequestMessageTimer?: ReturnType<typeof setTimeout>;
  private historicalRequestErrorTimer?: ReturnType<typeof setTimeout>;
  private historicalEditSuccessTimer?: ReturnType<typeof setTimeout>;
  private historicalEditErrorTimer?: ReturnType<typeof setTimeout>;

  dashboardData: any = null;

  morningSubmitting = false;
  eveningSubmitting = false;

  errorMessage = '';

  // Morning Work fields
  workDate = '';
  officeInTime = '';
  workingPoints = '';
  morningMessage = '';

  // Evening Work fields
  officeOutTime = '';
  pointsCompleted = '';
  pendingPoints = '';
  eveningMessage = '';
  eveningErrorMessage = '';

  // Historical Edit Request fields
  historicalEditReason = '';
  historicalRequestSubmitting = false;
  historicalRequestMessage = '';
  historicalRequestError = '';

  historicalEditRequests: any[] = [];
  historicalRequestsLoading = false;
  historicalRequestsError = '';

  // Approved Historical Work Editing
  approvedEditRequests: any[] = [];
  selectedApprovedRequestId: number | null = null;

  historicalEditForm = {
    office_in_time: '',
    working_points: '',
    office_out_time: '',
    points_completed: '',
    pending_points: '',
  };

  historicalEditSubmitting = false;
  historicalEditSuccess = '';
  historicalEditError = '';

  workHistory: any[] = [];
  selectedHistoricalWorkDate = '';
  historyLoading = false;
  historyError = '';
  historySearch = '';
  historyStartDate = '';
  historyEndDate = '';

  // Work History Pagination
  readonly historyPageSize = 5;
  historyPage = 1;

  // Historical Edit Requests Pagination
  readonly requestsPageSize = 5;
  requestsPage = 1;

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
    this.loadHistoricalEditRequests();
  }

  // Clear active timers when the component is destroyed
  ngOnDestroy(): void {
    clearTimeout(this.morningMessageTimer);
    clearTimeout(this.eveningMessageTimer);
    clearTimeout(this.errorMessageTimer);
    clearTimeout(this.eveningErrorMessageTimer);
    clearTimeout(this.historicalRequestMessageTimer);
    clearTimeout(this.historicalRequestErrorTimer);
    clearTimeout(this.historicalEditSuccessTimer);
    clearTimeout(this.historicalEditErrorTimer);
  }

  setTodayDate(): void {
    const today = new Date();
    this.workDate = today.toISOString().split('T')[0];
  }

  // Morning success message: hide after 5 seconds
  private showMorningMessage(message: string): void {
    this.morningMessage = message;

    clearTimeout(this.morningMessageTimer);

    this.morningMessageTimer = setTimeout(() => {
      this.morningMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Evening success message: hide after 5 seconds
  private showEveningMessage(message: string): void {
    this.eveningMessage = message;

    clearTimeout(this.eveningMessageTimer);

    this.eveningMessageTimer = setTimeout(() => {
      this.eveningMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // General error message: hide after 5 seconds
  private showErrorMessage(message: string): void {
    this.errorMessage = message;

    clearTimeout(this.errorMessageTimer);

    this.errorMessageTimer = setTimeout(() => {
      this.errorMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Evening error message: hide after 5 seconds
  private showEveningErrorMessage(message: string): void {
    this.eveningErrorMessage = message;

    clearTimeout(this.eveningErrorMessageTimer);

    this.eveningErrorMessageTimer = setTimeout(() => {
      this.eveningErrorMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Historical request success message: hide after 5 seconds
  private showHistoricalRequestMessage(message: string): void {
    this.historicalRequestMessage = message;

    clearTimeout(this.historicalRequestMessageTimer);

    this.historicalRequestMessageTimer = setTimeout(() => {
      this.historicalRequestMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Historical request error message: hide after 5 seconds
  private showHistoricalRequestError(message: string): void {
    this.historicalRequestError = message;

    clearTimeout(this.historicalRequestErrorTimer);

    this.historicalRequestErrorTimer = setTimeout(() => {
      this.historicalRequestError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Historical edit success message: hide after 5 seconds
  private showHistoricalEditSuccess(message: string): void {
    this.historicalEditSuccess = message;

    clearTimeout(this.historicalEditSuccessTimer);

    this.historicalEditSuccessTimer = setTimeout(() => {
      this.historicalEditSuccess = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  // Historical edit error message: hide after 5 seconds
  private showHistoricalEditError(message: string): void {
    this.historicalEditError = message;

    clearTimeout(this.historicalEditErrorTimer);

    this.historicalEditErrorTimer = setTimeout(() => {
      this.historicalEditError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  loadDashboard(): void {
    this.dailyWorkService.getDashboard().subscribe({
      next: (response) => {
        console.log('Dashboard data:', response);
        this.dashboardData = response;
        this.cdr.detectChanges();
      },

      error: (error) => {
        console.error('Dashboard loading failed:', error);
        this.showErrorMessage('Unable to load dashboard data.');
      },
    });
  }

  submitMorningWork(): void {
    if (this.morningSubmitting) {
      return;
    }

    this.morningMessage = '';
    this.errorMessage = '';

    if (!this.workDate || !this.officeInTime || !this.workingPoints.trim()) {
      this.showErrorMessage('Please fill all morning work fields.');
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
          console.error('Morning work submission failed:', error);

          this.showErrorMessage(error.error?.detail || 'Unable to submit morning work.');

          this.morningSubmitting = false;
          this.cdr.detectChanges();
        },
      });
  }

  submitEveningWork(): void {
    if (this.eveningSubmitting) {
      return;
    }

    this.eveningMessage = '';
    this.eveningErrorMessage = '';
    this.errorMessage = '';

    if (!this.workDate || !this.officeOutTime || !this.pointsCompleted.trim()) {
      this.showEveningErrorMessage('Please fill Work Date, Office Out Time, and Points Completed.');
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
          console.error('Evening work submission failed:', error);

          this.showEveningErrorMessage(error.error?.detail || 'Unable to submit evening work.');

          this.eveningSubmitting = false;
          this.cdr.detectChanges();
        },
      });
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/']);
  }

  submitHistoricalEditRequest(): void {
    if (this.historicalRequestSubmitting) {
      return;
    }

    this.historicalRequestMessage = '';
    this.historicalRequestError = '';

    if (!this.selectedHistoricalWorkDate || !this.historicalEditReason.trim()) {
      this.showHistoricalRequestError('Please select a work date and enter a reason.');
      return;
    }

    if (this.historicalEditReason.trim().length < 5) {
      this.showHistoricalRequestError('The reason must contain at least 5 characters.');
      return;
    }

    const selectedRecord = this.workHistory.find(
      (record: any) => record.work_date === this.selectedHistoricalWorkDate,
    );

    if (!selectedRecord) {
      this.showHistoricalRequestError(
        'Selected work record was not found. Please reload your history.',
      );
      return;
    }

    const dailyWorkId = selectedRecord.id;

    this.historicalRequestSubmitting = true;

    this.dailyWorkService
      .requestHistoricalEdit(dailyWorkId, this.historicalEditReason.trim())
      .subscribe({
        next: (response) => {
          this.showHistoricalRequestMessage(
            response?.message || 'Historical edit request submitted successfully.',
          );

          this.historicalRequestError = '';
          this.selectedHistoricalWorkDate = '';
          this.historicalEditReason = '';
          this.historicalRequestSubmitting = false;

          this.loadHistoricalEditRequests();
          this.cdr.detectChanges();
        },

        error: (error) => {
          this.showHistoricalRequestError(
            error.error?.detail || 'Unable to submit the historical edit request.',
          );

          this.historicalRequestMessage = '';
          this.historicalRequestSubmitting = false;
          this.cdr.detectChanges();
        },
      });
  }

  loadHistoricalEditRequests(): void {
    this.historicalRequestsLoading = true;
    this.historicalRequestsError = '';

    this.dailyWorkService.getHistoricalEditRequests().subscribe({
      next: (response: any) => {
        this.historicalEditRequests = response.requests ?? [];
        this.requestsPage = 1;
        this.historicalRequestsLoading = false;
        this.cdr.detectChanges();
      },

      error: (error: any) => {
        console.error('Historical edit requests loading failed:', error);

        this.historicalRequestsError =
          error.error?.detail || 'Unable to load historical edit requests.';

        this.historicalRequestsLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  get totalRequestsPages(): number {
    return Math.max(1, Math.ceil(this.historicalEditRequests.length / this.requestsPageSize));
  }

  get paginatedHistoricalEditRequests(): any[] {
    const start = (this.requestsPage - 1) * this.requestsPageSize;

    return this.historicalEditRequests.slice(start, start + this.requestsPageSize);
  }

  changeRequestsPage(page: number): void {
    if (page < 1 || page > this.totalRequestsPages) {
      return;
    }

    this.requestsPage = page;
  }

  get approvedHistoricalRequests(): any[] {
    return this.historicalEditRequests.filter(
      (request: any) => request.status === 'APPROVED' && !request.used_at,
    );
  }

  selectApprovedHistoricalRequest(requestId: number | null): void {
    this.selectedApprovedRequestId = requestId;
    this.historicalEditSuccess = '';
    this.historicalEditError = '';

    const request = this.approvedHistoricalRequests.find(
      (item: any) => item.request_id === requestId,
    );

    if (!request) {
      this.historicalEditForm = {
        office_in_time: '',
        working_points: '',
        office_out_time: '',
        points_completed: '',
        pending_points: '',
      };
      return;
    }

    const record = this.workHistory.find(
      (item: any) =>
        item.id === request.daily_work_id || item.daily_work_id === request.daily_work_id,
    );

    if (!record) {
      this.showHistoricalEditError(
        'The approved work record was not found. Please refresh your work history.',
      );
      return;
    }

    this.historicalEditForm = {
      office_in_time: record.office_in_time ?? '',
      working_points: record.working_points ?? '',
      office_out_time: record.office_out_time ?? '',
      points_completed: record.points_completed ?? '',
      pending_points: record.pending_points ?? '',
    };
  }

  submitHistoricalWorkEdit(): void {
    if (this.historicalEditSubmitting) {
      return;
    }

    this.historicalEditSuccess = '';
    this.historicalEditError = '';

    if (this.selectedApprovedRequestId === null) {
      this.showHistoricalEditError('Please select an approved historical edit request.');
      return;
    }

    const request = this.approvedHistoricalRequests.find(
      (item: any) => item.request_id === this.selectedApprovedRequestId,
    );

    if (!request) {
      this.showHistoricalEditError('This approval is no longer available. Refresh your requests.');
      return;
    }

    const record = this.workHistory.find(
      (item: any) =>
        item.id === request.daily_work_id || item.daily_work_id === request.daily_work_id,
    );

    if (!record) {
      this.showHistoricalEditError('The historical work record could not be found.');
      return;
    }

    this.historicalEditSubmitting = true;

    this.dailyWorkService
      .editHistoricalWork(record.id ?? record.daily_work_id, {
        office_in_time: this.historicalEditForm.office_in_time,
        working_points: this.historicalEditForm.working_points,
        office_out_time: this.historicalEditForm.office_out_time,
        points_completed: this.historicalEditForm.points_completed,
        pending_points: this.historicalEditForm.pending_points,
      })
      .subscribe({
        next: (response: any) => {
          this.historicalEditSubmitting = false;

          this.showHistoricalEditSuccess(
            response?.message ?? 'Historical work updated successfully.',
          );

          this.selectedApprovedRequestId = null;

          this.historicalEditForm = {
            office_in_time: '',
            working_points: '',
            office_out_time: '',
            points_completed: '',
            pending_points: '',
          };

          this.loadWorkHistory();
          this.loadHistoricalEditRequests();
          this.loadDashboard();
          this.cdr.detectChanges();
        },

        error: (error: any) => {
          console.error('Historical work edit failed:', error);

          this.historicalEditSubmitting = false;

          this.showHistoricalEditError(error.error?.detail ?? 'Unable to update historical work.');

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
        this.historyPage = 1;
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

      if (this.historyStartDate && recordDate < this.historyStartDate) {
        return false;
      }

      if (this.historyEndDate && recordDate > this.historyEndDate) {
        return false;
      }

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

  get totalHistoryPages(): number {
    return Math.max(1, Math.ceil(this.filteredWorkHistory.length / this.historyPageSize));
  }

  get paginatedWorkHistory(): any[] {
    const start = (this.historyPage - 1) * this.historyPageSize;

    return this.filteredWorkHistory.slice(start, start + this.historyPageSize);
  }

  changeHistoryPage(page: number): void {
    if (page < 1 || page > this.totalHistoryPages) {
      return;
    }

    this.historyPage = page;
  }

  clearHistoryFilters(): void {
    this.historySearch = '';
    this.historyStartDate = '';
    this.historyEndDate = '';
    this.historyPage = 1;
  }
}
