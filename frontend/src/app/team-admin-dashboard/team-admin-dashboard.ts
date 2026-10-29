import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe, JsonPipe } from '@angular/common';
import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-team-admin-dashboard',
  standalone: true,
  imports: [FormsModule, DatePipe, JsonPipe],
  templateUrl: './team-admin-dashboard.html',
  styleUrl: './team-admin-dashboard.css',
})
export class TeamAdminDashboard implements OnInit, OnDestroy {
  user: any = null;

  summary = {
    total_work_days: 0,
    completed_days: 0,
    pending_days: 0,
    latest_work_date: null as string | null,
  };

  workHistory: any[] = [];
  teamMembers: any[] = [];

  historicalEditRequests: any[] = [];
  historicalWorkAudit: any[] = [];

  historicalRequestsLoading = false;
  historicalRequestsError = '';
  reviewingRequestId: number | null = null;
  reviewComments: Record<number, string> = {};

  historicalAuditLoading = false;
  historicalAuditError = '';

  dashboardLoading = false;
  historyLoading = false;
  membersLoading = false;

  dashboardError = '';
  historyError = '';
  membersError = '';
  memberStatusMessage = '';

  memberSearch = '';

  historySearch = '';
  historyStartDate = '';
  historyEndDate = '';

  requestSearch = '';
  requestStatusFilter = '';
  requestStartDate = '';
  requestEndDate = '';

  auditSearch = '';
  auditStartDate = '';
  auditEndDate = '';

  updatingMemberId: number | null = null;

  // Pagination: 5 records per page
  readonly membersPageSize = 5;
  membersPage = 1;

  readonly historyPageSize = 5;
  historyPage = 1;

  readonly requestsPageSize = 5;
  requestsPage = 1;

  readonly auditPageSize = 5;
  auditPage = 1;

  private messageTimers: Partial<
    Record<
      'dashboardError' | 'historyError' | 'membersError' | 'memberStatusMessage',
      ReturnType<typeof setTimeout>
    >
  > = {};

  constructor(
    private dailyWorkService: DailyWorkService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.loadWorkHistory();
    this.loadTeamMembers();
    this.loadHistoricalEditRequests();
    this.loadHistoricalWorkAudit();
  }

  ngOnDestroy(): void {
    Object.values(this.messageTimers).forEach((timer) => {
      if (timer) clearTimeout(timer);
    });
    this.messageTimers = {};
  }

  private showMessage(
    message: string,
    field: 'dashboardError' | 'historyError' | 'membersError' | 'memberStatusMessage',
  ): void {
    this.clearMessage(field);

    if (field === 'dashboardError') this.dashboardError = message;
    if (field === 'historyError') this.historyError = message;
    if (field === 'membersError') this.membersError = message;
    if (field === 'memberStatusMessage') this.memberStatusMessage = message;

    this.cdr.detectChanges();

    this.messageTimers[field] = setTimeout(() => {
      if (field === 'dashboardError') this.dashboardError = '';
      if (field === 'historyError') this.historyError = '';
      if (field === 'membersError') this.membersError = '';
      if (field === 'memberStatusMessage') this.memberStatusMessage = '';

      delete this.messageTimers[field];
      this.cdr.detectChanges();
    }, 5000);
  }

  private clearMessage(
    field: 'dashboardError' | 'historyError' | 'membersError' | 'memberStatusMessage',
  ): void {
    const timer = this.messageTimers[field];

    if (timer) clearTimeout(timer);
    delete this.messageTimers[field];

    if (field === 'dashboardError') this.dashboardError = '';
    if (field === 'historyError') this.historyError = '';
    if (field === 'membersError') this.membersError = '';
    if (field === 'memberStatusMessage') this.memberStatusMessage = '';
  }

  // ---------- DASHBOARD ----------

  loadDashboard(): void {
    if (this.dashboardLoading) return;

    this.dashboardLoading = true;
    this.clearMessage('dashboardError');

    this.dailyWorkService
      .getDashboard()
      .pipe(
        finalize(() => {
          this.dashboardLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.user = response.user ?? null;

          this.summary = {
            total_work_days: response.summary?.total_work_days ?? 0,
            completed_days: response.summary?.completed_days ?? 0,
            pending_days: response.summary?.pending_days ?? 0,
            latest_work_date: response.summary?.latest_work_date ?? null,
          };
        },
        error: (error: any) => {
          console.error('Dashboard loading failed:', error);
          this.showMessage('Unable to load dashboard information.', 'dashboardError');
        },
      });
  }

  // ---------- TEAM WORK HISTORY ----------

  loadWorkHistory(): void {
    if (this.historyLoading) return;

    this.historyLoading = true;
    this.clearMessage('historyError');

    this.dailyWorkService
      .getTeamWorkHistory()
      .pipe(
        finalize(() => {
          this.historyLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.workHistory = response.work ?? [];
          this.historyPage = 1;
        },
        error: (error: any) => {
          console.error('Team work history loading failed:', error);
          this.showMessage('Unable to load team work history.', 'historyError');
        },
      });
  }

  get filteredWorkHistory(): any[] {
    const search = this.historySearch.trim().toLowerCase();

    return this.workHistory.filter((record: any) => {
      const recordDate = String(record.work_date ?? '').substring(0, 10);

      const matchesStartDate = !this.historyStartDate || recordDate >= this.historyStartDate;

      const matchesEndDate = !this.historyEndDate || recordDate <= this.historyEndDate;

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

      return matchesStartDate && matchesEndDate && (!search || searchableText.includes(search));
    });
  }

  get paginatedWorkHistory(): any[] {
    const start = (this.historyPage - 1) * this.historyPageSize;
    return this.filteredWorkHistory.slice(start, start + this.historyPageSize);
  }

  get totalHistoryPages(): number {
    return Math.max(1, Math.ceil(this.filteredWorkHistory.length / this.historyPageSize));
  }

  changeHistoryPage(page: number): void {
    if (page >= 1 && page <= this.totalHistoryPages) {
      this.historyPage = page;
    }
  }

  clearHistoryFilters(): void {
    this.historySearch = '';
    this.historyStartDate = '';
    this.historyEndDate = '';
    this.historyPage = 1;
  }

  refreshWorkHistory(): void {
    this.loadWorkHistory();
  }

  // ---------- HISTORICAL EDIT REQUESTS ----------

  loadHistoricalEditRequests(): void {
    if (this.historicalRequestsLoading) return;

    this.historicalRequestsLoading = true;
    this.historicalRequestsError = '';

    this.dailyWorkService
      .getHistoricalEditRequests()
      .pipe(
        finalize(() => {
          this.historicalRequestsLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.historicalEditRequests = response.requests ?? [];
          this.requestsPage = 1;
        },
        error: (error: any) => {
          console.error('Historical edit requests loading failed:', error);
          this.historicalRequestsError =
            error?.error?.detail ?? 'Unable to load historical edit requests.';
        },
      });
  }

  get filteredHistoricalEditRequests(): any[] {
    const search = this.requestSearch.trim().toLowerCase();

    return this.historicalEditRequests.filter((request: any) => {
      const requestDate = String(
        request.work_date ??
          request.request_date ??
          request.created_at ??
          request.requested_at ??
          '',
      ).substring(0, 10);

      const searchableText = [
        request.user_name,
        request.user_email,
        request.status,
        request.work_date,
        request.request_date,
        request.created_at,
        request.requested_at,
        request.reason,
        request.request_reason,
        request.requested_changes,
        request.request_id,
      ]
        .filter((value: any) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();

      const matchesSearch = !search || searchableText.includes(search);

      const matchesStatus =
        !this.requestStatusFilter ||
        String(request.status ?? '').toUpperCase() === this.requestStatusFilter.toUpperCase();

      const matchesStartDate = !this.requestStartDate || requestDate >= this.requestStartDate;

      const matchesEndDate = !this.requestEndDate || requestDate <= this.requestEndDate;

      return matchesSearch && matchesStatus && matchesStartDate && matchesEndDate;
    });
  }

  get paginatedHistoricalEditRequests(): any[] {
    const start = (this.requestsPage - 1) * this.requestsPageSize;
    return this.filteredHistoricalEditRequests.slice(start, start + this.requestsPageSize);
  }

  get totalRequestsPages(): number {
    return Math.max(
      1,
      Math.ceil(this.filteredHistoricalEditRequests.length / this.requestsPageSize),
    );
  }

  changeRequestsPage(page: number): void {
    if (page >= 1 && page <= this.totalRequestsPages) {
      this.requestsPage = page;
    }
  }

  clearRequestFilters(): void {
    this.requestSearch = '';
    this.requestStatusFilter = '';
    this.requestStartDate = '';
    this.requestEndDate = '';
    this.requestsPage = 1;
  }

  reviewHistoricalRequest(request: any, status: 'APPROVED' | 'REJECTED'): void {
    if (this.reviewingRequestId !== null) return;
    if (request.status !== 'PENDING') return;

    const reviewComment = (this.reviewComments[request.request_id] ?? '').trim();

    this.reviewingRequestId = request.request_id;
    this.historicalRequestsError = '';

    this.dailyWorkService
      .reviewHistoricalEdit(request.request_id, status, reviewComment)
      .subscribe({
        next: () => {
          this.reviewingRequestId = null;
          this.loadHistoricalEditRequests();
        },
        error: (error: any) => {
          console.error('Historical request review failed:', error);

          this.historicalRequestsError =
            error?.error?.detail ?? 'Unable to review the historical edit request.';

          this.reviewingRequestId = null;
          this.cdr.detectChanges();
        },
      });
  }

  // ---------- HISTORICAL WORK AUDIT ----------

  loadHistoricalWorkAudit(): void {
    if (this.historicalAuditLoading) return;

    this.historicalAuditLoading = true;
    this.historicalAuditError = '';

    this.dailyWorkService
      .getHistoricalWorkAudit()
      .pipe(
        finalize(() => {
          this.historicalAuditLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.historicalWorkAudit = response.audit_logs ?? [];
          this.auditPage = 1;
        },
        error: (error: any) => {
          console.error('Historical work audit loading failed:', error);

          this.historicalAuditError =
            error?.error?.detail ?? 'Unable to load historical work audit logs.';
        },
      });
  }

  get filteredHistoricalWorkAudit(): any[] {
    const search = this.auditSearch.trim().toLowerCase();

    return this.historicalWorkAudit.filter((audit: any) => {
      const auditDate = String(
        audit.edited_at ?? audit.work_date ?? audit.created_at ?? '',
      ).substring(0, 10);

      const searchableText = [
        audit.user_name,
        audit.user_email,
        audit.edited_by_name,
        audit.edited_by_email,
        audit.work_date,
        audit.edited_at,
        audit.action,
        audit.old_values,
        audit.new_values,
        audit.edit_request_id,
        audit.daily_work_id,
      ]
        .filter((value: any) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();

      const matchesSearch = !search || searchableText.includes(search);

      const matchesStartDate = !this.auditStartDate || auditDate >= this.auditStartDate;

      const matchesEndDate = !this.auditEndDate || auditDate <= this.auditEndDate;

      return matchesSearch && matchesStartDate && matchesEndDate;
    });
  }

  get paginatedHistoricalWorkAudit(): any[] {
    const start = (this.auditPage - 1) * this.auditPageSize;
    return this.filteredHistoricalWorkAudit.slice(start, start + this.auditPageSize);
  }

  get totalAuditPages(): number {
    return Math.max(1, Math.ceil(this.filteredHistoricalWorkAudit.length / this.auditPageSize));
  }

  changeAuditPage(page: number): void {
    if (page >= 1 && page <= this.totalAuditPages) {
      this.auditPage = page;
    }
  }

  clearAuditFilters(): void {
    this.auditSearch = '';
    this.auditStartDate = '';
    this.auditEndDate = '';
    this.auditPage = 1;
  }

  refreshHistoricalWorkAudit(): void {
    this.loadHistoricalWorkAudit();
  }

  // ---------- TEAM MEMBER MANAGEMENT ----------

  loadTeamMembers(): void {
    if (this.membersLoading) return;

    this.membersLoading = true;
    this.clearMessage('membersError');

    this.dailyWorkService
      .getTeamMembers()
      .pipe(
        finalize(() => {
          this.membersLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.teamMembers = response.members ?? [];
          this.membersPage = 1;
        },
        error: (error: any) => {
          console.error('Team member loading failed:', error);

          this.showMessage(error?.error?.detail ?? 'Unable to load team members.', 'membersError');
        },
      });
  }

  get filteredTeamMembers(): any[] {
    const search = this.memberSearch.trim().toLowerCase();

    return this.teamMembers.filter((member: any) => {
      const searchableText = [member.name, member.email, member.team_name]
        .filter((value: any) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();

      return !search || searchableText.includes(search);
    });
  }

  get paginatedTeamMembers(): any[] {
    const start = (this.membersPage - 1) * this.membersPageSize;
    return this.filteredTeamMembers.slice(start, start + this.membersPageSize);
  }

  get totalMembersPages(): number {
    return Math.max(1, Math.ceil(this.filteredTeamMembers.length / this.membersPageSize));
  }

  changeMembersPage(page: number): void {
    if (page >= 1 && page <= this.totalMembersPages) {
      this.membersPage = page;
    }
  }

  toggleMemberStatus(member: any): void {
    if (this.updatingMemberId !== null) return;

    const newStatus = !member.is_activate;
    const action = newStatus ? 'activated' : 'deactivated';

    this.updatingMemberId = member.user_id;
    this.clearMessage('membersError');
    this.clearMessage('memberStatusMessage');

    this.dailyWorkService.updateUserStatus(member.user_id, newStatus).subscribe({
      next: (response: any) => {
        member.is_activate = response.is_activate ?? newStatus;
        this.updatingMemberId = null;

        this.showMessage(
          `${member.name}'s account has been ${action} successfully.`,
          'memberStatusMessage',
        );
      },
      error: (error: any) => {
        console.error('Member status update failed:', error);
        this.updatingMemberId = null;

        this.showMessage(error?.error?.detail ?? 'Unable to update member status.', 'membersError');
      },
    });
  }

  get totalMembers(): number {
    return this.teamMembers.length;
  }

  get activeMembersCount(): number {
    return this.teamMembers.filter((member: any) => member.is_activate === true).length;
  }

  get inactiveMembersCount(): number {
    return this.teamMembers.filter((member: any) => member.is_activate === false).length;
  }

  logout(): void {
    this.authService.logout();
  }
}
