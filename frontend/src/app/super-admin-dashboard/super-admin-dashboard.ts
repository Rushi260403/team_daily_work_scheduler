import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { DatePipe, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DailyWorkService } from '../services/daily-work';
import { AuthService } from '../services/auth';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-super-admin-dashboard',
  standalone: true,
  imports: [FormsModule, DatePipe, JsonPipe],
  templateUrl: './super-admin-dashboard.html',
  styleUrl: './super-admin-dashboard.css',
})
export class SuperAdminDashboard implements OnInit {
  user: any = null;

  summary = {
    total_work_days: 0,
    completed_days: 0,
    pending_days: 0,
    latest_work_date: null as string | null,
  };

  workHistory: any[] = [];

  // All Teams Work History pagination
  readonly historyPageSize = 5;
  historyPage = 1;

  // Historical Edit Requests
  historicalEditRequests: any[] = [];

  // Historical Edit Requests pagination
  readonly requestsPageSize = 5;
  requestsPage = 1;

  // Historical Edit Requests filters
  requestsSearch = '';
  requestsStatus = '';
  requestsTeam = '';
  requestsStartDate = '';
  requestsEndDate = '';

  historicalRequestsLoading = false;
  historicalRequestsError = '';
  historicalRequestMessage = '';
  historicalRequestError = '';

  reviewComments: { [requestId: number]: string } = {};
  reviewingRequestId: number | null = null;

  // Historical Work Audit
  historicalAuditRecords: any[] = [];

  // Historical Work Audit pagination
  readonly auditPageSize = 5;
  auditPage = 1;

  // Historical Work Audit filters
  auditSearch = '';
  auditTeam = '';
  auditStartDate = '';
  auditEndDate = '';

  historicalAuditLoading = false;
  historicalAuditError = '';

  users: any[] = [];
  totalUsers = 0;
  userSearch = '';
  selectedUserRole = '';
  selectedUserTeam = '';
  selectedUserStatus = '';
  usersLoading = false;
  usersError = '';

  // Registered Accounts pagination
  readonly pageSize = 5;
  usersPage = 1;

  teams: any[] = [];

  // Change User Team
  userTeamSelections: { [userId: number]: string } = {};
  updatingTeamUserId: number | null = null;
  userActionMessage = '';
  userActionError = '';

  historySearch = '';
  historyStartDate = '';
  historyEndDate = '';

  selectedTeam = '';
  selectedRole = '';

  dashboardLoading = false;
  historyLoading = false;

  dashboardError = '';
  historyError = '';

  // Add Team form
  showAddTeamForm = false;

  newTeam = {
    team_name: '',
    academic_year: '',
    description: '',
  };

  teamSaving = false;
  teamActionMessage = '';
  teamActionError = '';

  private teamActionMessageTimeout: ReturnType<typeof setTimeout> | null = null;
  private teamActionErrorTimeout: ReturnType<typeof setTimeout> | null = null;

  // Edit Team form
  editingTeamId: number | null = null;

  editTeamForm = {
    team_name: '',
    academic_year: '',
    description: '',
    is_activate: true,
  };

  teamUpdating = false;

  updatingStatusUserId: number | null = null;
  paginatedEditRequests: any;

  constructor(
    private dailyWorkService: DailyWorkService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
    this.loadWorkHistory();
    this.loadUsers();
    this.loadTeams();
    this.loadHistoricalEditRequests();
    this.loadHistoricalWorkAudit();
  }

  private userActionMessageTimeout: ReturnType<typeof setTimeout> | null = null;

  private userActionErrorTimeout: ReturnType<typeof setTimeout> | null = null;

  loadDashboard(): void {
    this.dashboardLoading = true;
    this.dashboardError = '';

    this.dailyWorkService.getAdminOverallSummary().subscribe({
      next: (response: any) => {
        this.summary = {
          total_work_days: response.daily_work?.total_work_records ?? 0,
          completed_days: response.daily_work?.completed_days ?? 0,
          pending_days: response.daily_work?.pending_days ?? 0,
          latest_work_date: response.daily_work?.latest_work_date ?? null,
        };

        this.dashboardLoading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Super Admin overall summary loading failed:', error);
        this.dashboardError = 'Unable to load overall organization summary.';
        this.dashboardLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  loadWorkHistory(): void {
    this.historyLoading = true;
    this.historyError = '';

    this.dailyWorkService.getAllWorkHistory().subscribe({
      next: (response: any) => {
        this.workHistory = response.daily_work ?? [];
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('All work history loading failed:', error);
        this.historyError = 'Unable to load work history.';
        this.historyLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  get availableTeams(): string[] {
    return [
      ...new Set(
        this.workHistory.map((record: any) => record.team_name).filter((team: any) => !!team),
      ),
    ].sort();
  }

  get availableRoles(): string[] {
    return [
      ...new Set(
        this.workHistory.map((record: any) => record.user_role).filter((role: any) => !!role),
      ),
    ].sort();
  }

  get filteredWorkHistory(): any[] {
    const search = this.historySearch.trim().toLowerCase();

    return this.workHistory.filter((record: any) => {
      const recordDate = record.work_date ?? '';

      const matchesStartDate = !this.historyStartDate || recordDate >= this.historyStartDate;

      const matchesEndDate = !this.historyEndDate || recordDate <= this.historyEndDate;

      const matchesTeam = !this.selectedTeam || record.team_name === this.selectedTeam;

      const matchesRole = !this.selectedRole || record.user_role === this.selectedRole;

      const searchableText = [
        record.user_name,
        record.user_email,
        record.team_name,
        record.user_role,
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
        matchesTeam &&
        matchesRole &&
        (!search || searchableText.includes(search))
      );
    });
  }

  // Return only the work-history records for the current page.
  get paginatedWorkHistory(): any[] {
    const startIndex = (this.historyPage - 1) * this.historyPageSize;

    return this.filteredWorkHistory.slice(startIndex, startIndex + this.historyPageSize);
  }

  // Return only the historical edit requests for the current page.
  get paginatedHistoricalRequests(): any[] {
    const startIndex = (this.requestsPage - 1) * this.requestsPageSize;

    return this.filteredHistoricalRequests.slice(startIndex, startIndex + this.requestsPageSize);
  }

  // Filter historical edit requests by search, status, team, and work date.
  get filteredHistoricalRequests(): any[] {
    const search = this.requestsSearch.trim().toLowerCase();

    return this.historicalEditRequests.filter((request: any) => {
      const searchableText = [
        request.requester_name,
        request.requester_email,
        request.requester_id,
        request.team_name,
        request.requester_role,
        request.request_reason,
      ]
        .filter((value) => value !== null && value !== undefined)
        .join(' ')
        .toLowerCase();

      const matchesSearch = !search || searchableText.includes(search);

      const matchesStatus = !this.requestsStatus || request.status === this.requestsStatus;

      const matchesTeam = !this.requestsTeam || request.team_name === this.requestsTeam;

      const workDate = request.work_date ? String(request.work_date).slice(0, 10) : '';

      const matchesStartDate =
        !this.requestsStartDate || (workDate !== '' && workDate >= this.requestsStartDate);

      const matchesEndDate =
        !this.requestsEndDate || (workDate !== '' && workDate <= this.requestsEndDate);

      return matchesSearch && matchesStatus && matchesTeam && matchesStartDate && matchesEndDate;
    });
  }

  // Available teams for the team filter.
  get historicalRequestTeams(): string[] {
    return [
      ...new Set(
        this.historicalEditRequests
          .map((request: any) => request.team_name)
          .filter((team: any) => typeof team === 'string' && team.trim() !== ''),
      ),
    ].sort();
  }

  // Calculate the total number of historical edit-request pages.
  get requestsTotalPages(): number {
    return Math.max(1, Math.ceil(this.filteredHistoricalRequests.length / this.requestsPageSize));
  }

  // Go to the previous historical edit-request page.
  previousRequestsPage(): void {
    if (this.requestsPage > 1) {
      this.requestsPage--;
    }
  }

  // Go to the next historical edit-request page.
  nextRequestsPage(): void {
    if (this.requestsPage < this.requestsTotalPages) {
      this.requestsPage++;
    }
  }

  // Calculate the total number of work-history pages.
  get historyTotalPages(): number {
    return Math.max(1, Math.ceil(this.filteredWorkHistory.length / this.historyPageSize));
  }

  // Go to the previous work-history page.
  previousHistoryPage(): void {
    if (this.historyPage > 1) {
      this.historyPage--;
    }
  }

  // Go to the next work-history page.
  nextHistoryPage(): void {
    if (this.historyPage < this.historyTotalPages) {
      this.historyPage++;
    }
  }

  // Filter audit records by search, team, and work-date range.
  get filteredHistoricalAudit(): any[] {
    const search = this.auditSearch.trim().toLowerCase();

    return this.historicalAuditRecords.filter((audit: any) => {
      const searchableText = [
        audit.work_owner_name,
        audit.work_owner_id,
        audit.team_name,
        audit.editor_name,
        audit.edited_by,
        audit.reviewer_name,
        audit.reviewed_by,
        audit.edit_request_id,
        audit.old_values,
        audit.new_values,
      ]
        .filter((value) => value !== null && value !== undefined)
        .map((value) => (typeof value === 'object' ? JSON.stringify(value) : String(value)))
        .join(' ')
        .toLowerCase();

      const matchesSearch = !search || searchableText.includes(search);

      const matchesTeam = !this.auditTeam || audit.team_name === this.auditTeam;

      const workDate = audit.work_date ? String(audit.work_date).slice(0, 10) : '';

      const matchesStartDate =
        !this.auditStartDate || (workDate !== '' && workDate >= this.auditStartDate);

      const matchesEndDate =
        !this.auditEndDate || (workDate !== '' && workDate <= this.auditEndDate);

      return matchesSearch && matchesTeam && matchesStartDate && matchesEndDate;
    });
  }

  // Available teams for the audit team filter.
  get historicalAuditTeams(): string[] {
    return [
      ...new Set(
        this.historicalAuditRecords
          .map((audit: any) => audit.team_name)
          .filter((team: any) => typeof team === 'string' && team.trim() !== ''),
      ),
    ].sort();
  }

  // Return only the audit records for the current page.
  get paginatedHistoricalAudit(): any[] {
    const startIndex = (this.auditPage - 1) * this.auditPageSize;

    return this.filteredHistoricalAudit.slice(startIndex, startIndex + this.auditPageSize);
  }

  // Calculate the total number of audit pages.
  get auditTotalPages(): number {
    return Math.max(1, Math.ceil(this.filteredHistoricalAudit.length / this.auditPageSize));
  }

  // Go to the previous audit page.
  previousAuditPage(): void {
    if (this.auditPage > 1) {
      this.auditPage--;
    }
  }

  // Go to the next audit page.
  nextAuditPage(): void {
    if (this.auditPage < this.auditTotalPages) {
      this.auditPage++;
    }
  }

  loadUsers(): void {
    if (this.usersLoading) {
      return;
    }

    this.usersLoading = true;
    this.usersError = '';

    this.dailyWorkService
      .getAllUsers()
      .pipe(
        finalize(() => {
          this.usersLoading = false;
          this.cdr.detectChanges();
        }),
      )
      .subscribe({
        next: (response: any) => {
          this.users = response.users ?? [];
          this.totalUsers = response.total_users ?? this.users.length;

          // Initialize each user's team selection.
          this.userTeamSelections = {};

          for (const account of this.users) {
            if (account.team_id !== null && account.team_id !== undefined) {
              this.userTeamSelections[account.id] = String(account.team_id);
            } else {
              this.userTeamSelections[account.id] = '';
            }
          }
        },
        error: (error: any) => {
          console.error('User list loading failed:', error);
          this.usersError = error?.error?.detail || 'Unable to load users.';
        },
      });
  }

  get availableUserRoles(): string[] {
    return [
      ...new Set(this.users.map((account: any) => account.role).filter((role: any) => !!role)),
    ].sort();
  }

  get availableUserTeams(): number[] {
    return [
      ...new Set(
        this.users
          .map((account: any) => account.team_id)
          .filter((teamId: any) => teamId !== null && teamId !== undefined),
      ),
    ].sort((a, b) => a - b);
  }

  getTeamName(teamId: number | null): string {
    if (teamId === null || teamId === undefined) {
      return 'Unassigned';
    }

    const team = this.teams.find((item: any) => item.id === teamId);

    return team?.team_name ?? `Team ${teamId}`;
  }

  get filteredUsers(): any[] {
    const search = this.userSearch.trim().toLowerCase();

    return this.users.filter((account: any) => {
      const matchesSearch =
        !search ||
        (account.name ?? '').toLowerCase().includes(search) ||
        (account.email ?? '').toLowerCase().includes(search);

      const matchesRole = !this.selectedUserRole || account.role === this.selectedUserRole;

      const matchesTeam =
        !this.selectedUserTeam || String(account.team_id) === this.selectedUserTeam;

      const matchesStatus =
        !this.selectedUserStatus ||
        (this.selectedUserStatus === 'active' ? account.is_activate : !account.is_activate);

      return matchesSearch && matchesRole && matchesTeam && matchesStatus;
    });
  }

  // Return only the accounts for the current page.
  get paginatedUsers(): any[] {
    const startIndex = (this.usersPage - 1) * this.pageSize;

    return this.filteredUsers.slice(startIndex, startIndex + this.pageSize);
  }

  // Calculate the total number of pages.
  get usersTotalPages(): number {
    return Math.max(1, Math.ceil(this.filteredUsers.length / this.pageSize));
  }

  // Go to the previous page.
  previousUsersPage(): void {
    if (this.usersPage > 1) {
      this.usersPage--;
    }
  }

  // Go to the next page.
  nextUsersPage(): void {
    if (this.usersPage < this.usersTotalPages) {
      this.usersPage++;
    }
  }

  clearUserFilters(): void {
    this.userSearch = '';
    this.selectedUserRole = '';
    this.selectedUserTeam = '';
    this.selectedUserStatus = '';
    // Return to the first page after clearing filters.
    this.usersPage = 1;
  }

  // Step 2.2: Save a user's new team.
  changeUserTeam(account: any): void {
    const selectedTeamId = this.userTeamSelections[account.id];

    if (!selectedTeamId) {
      this.userActionError = 'Please select a team first.';
      this.userActionMessage = '';
      return;
    }

    const teamId = Number(selectedTeamId);

    if (!Number.isInteger(teamId) || teamId <= 0) {
      this.userActionError = 'Please select a valid team.';
      this.userActionMessage = '';
      return;
    }

    if (Number(account.team_id) === teamId) {
      this.userActionMessage = 'This user is already assigned to that team.';
      this.userActionError = '';
      return;
    }

    this.updatingTeamUserId = account.id;
    this.userActionMessage = '';
    this.userActionError = '';

    this.dailyWorkService.updateUserTeam(account.id, teamId).subscribe({
      next: () => {
        this.userActionMessage = `Team updated successfully for ${account.name}.`;
        this.userActionError = '';
        this.updatingTeamUserId = null;

        // Clear any previous success-message timeout.
        if (this.userActionMessageTimeout) {
          clearTimeout(this.userActionMessageTimeout);
        }

        // Hide the success message after 5 seconds.
        this.userActionMessageTimeout = setTimeout(() => {
          this.userActionMessage = '';
          this.cdr.detectChanges();
        }, 5000);

        // Reload users to display the saved assignment.
        this.loadUsers();
      },
      error: (error: any) => {
        this.updatingTeamUserId = null;
        this.userActionMessage = '';

        this.userActionError =
          error?.error?.detail || 'Unable to update the user team. Please try again.';

        // Clear any previous error-message timeout.
        if (this.userActionErrorTimeout) {
          clearTimeout(this.userActionErrorTimeout);
        }

        // Hide the error message after 5 seconds.
        this.userActionErrorTimeout = setTimeout(() => {
          this.userActionError = '';
          this.cdr.detectChanges();
        }, 5000);

        this.cdr.detectChanges();
      },
    });
  }

  clearHistoryFilters(): void {
    this.historySearch = '';
    this.historyStartDate = '';
    this.historyEndDate = '';
    this.selectedTeam = '';
    this.selectedRole = '';

    // Return to the first page after clearing filters.
    this.historyPage = 1;
  }

  refreshWorkHistory(): void {
    this.loadWorkHistory();
  }

  logout(): void {
    this.authService.logout();
  }

  loadTeams(): void {
    this.dailyWorkService.getAllTeams().subscribe({
      next: (response: any) => {
        this.teams = response.teams ?? [];
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('Team list loading failed:', error);
      },
    });
  }

  toggleAddTeamForm(): void {
    this.showAddTeamForm = !this.showAddTeamForm;
    this.teamActionError = '';

    if (!this.showAddTeamForm) {
      this.resetNewTeamForm();
    }
  }

  resetNewTeamForm(): void {
    this.newTeam = {
      team_name: '',
      academic_year: '',
      description: '',
    };
  }

  createTeam(): void {
    const teamName = this.newTeam.team_name.trim();
    const academicYear = this.newTeam.academic_year.trim();
    const description = this.newTeam.description.trim();

    if (!teamName || !academicYear) {
      this.showTeamError('Team name and academic year are required.');
      return;
    }

    this.teamSaving = true;
    this.teamActionError = '';
    this.teamActionMessage = '';

    this.dailyWorkService
      .createTeam({
        team_name: teamName,
        academic_year: academicYear,
        description,
      })
      .subscribe({
        next: () => {
          this.teamSaving = false;
          this.showTeamSuccess('Team created successfully.');
          this.resetNewTeamForm();
          this.showAddTeamForm = false;
          this.loadTeams();
        },
        error: (error: any) => {
          this.teamSaving = false;
          this.showTeamError(error?.error?.detail || 'Unable to create team. Please try again.');
          this.cdr.detectChanges();
        },
      });
  }

  private showTeamSuccess(message: string): void {
    this.teamActionMessage = message;
    this.teamActionError = '';

    if (this.teamActionMessageTimeout) {
      clearTimeout(this.teamActionMessageTimeout);
    }

    this.teamActionMessageTimeout = setTimeout(() => {
      this.teamActionMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  private showTeamError(message: string): void {
    this.teamActionError = message;
    this.teamActionMessage = '';

    if (this.teamActionErrorTimeout) {
      clearTimeout(this.teamActionErrorTimeout);
    }

    this.teamActionErrorTimeout = setTimeout(() => {
      this.teamActionError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  startEditTeam(team: any): void {
    this.editingTeamId = team.id;

    this.editTeamForm = {
      team_name: team.team_name ?? '',
      academic_year: team.academic_year ?? '',
      description: team.description ?? '',
      is_activate: team.is_activate !== false,
    };

    this.teamActionMessage = '';
    this.teamActionError = '';
  }

  cancelEditTeam(): void {
    this.editingTeamId = null;
    this.editTeamForm = {
      team_name: '',
      academic_year: '',
      description: '',
      is_activate: true,
    };
  }

  saveTeamChanges(): void {
    if (this.editingTeamId === null) {
      return;
    }

    const teamName = this.editTeamForm.team_name.trim();
    const academicYear = this.editTeamForm.academic_year.trim();

    if (!teamName || !academicYear) {
      this.showTeamError('Team name and academic year are required.');
      return;
    }

    this.teamUpdating = true;
    this.teamActionMessage = '';
    this.teamActionError = '';

    this.dailyWorkService
      .updateTeam(this.editingTeamId, {
        team_name: teamName,
        academic_year: academicYear,
        description: this.editTeamForm.description.trim(),
        is_activate: this.editTeamForm.is_activate,
      })
      .subscribe({
        next: () => {
          this.teamUpdating = false;
          this.editingTeamId = null;
          this.showTeamSuccess('Team updated successfully.');
          this.loadTeams();
        },
        error: (error: any) => {
          this.teamUpdating = false;
          this.showTeamError(error?.error?.detail || 'Unable to update team. Please try again.');
          this.cdr.detectChanges();
        },
      });
  }

  toggleTeamStatus(team: any): void {
    const newStatus = !team.is_activate;

    const action = newStatus ? 'activate' : 'deactivate';

    this.dailyWorkService
      .updateTeam(team.id, {
        team_name: team.team_name,
        academic_year: team.academic_year,
        description: team.description ?? '',
        is_activate: newStatus,
      })
      .subscribe({
        next: (response: any) => {
          this.showTeamSuccess(`Team ${action}d successfully.`);

          // Automatically refresh both sections
          this.loadTeams();
          this.loadUsers();

          // Refresh dashboard statistics if applicable
          this.loadDashboard();
        },
        error: (error: any) => {
          this.showTeamError(error?.error?.detail || `Failed to ${action} team.`);
        },
      });
  }

  private showUserSuccess(message: string): void {
    this.userActionMessage = message;
    this.userActionError = '';

    if (this.userActionMessageTimeout) {
      clearTimeout(this.userActionMessageTimeout);
    }

    this.userActionMessageTimeout = setTimeout(() => {
      this.userActionMessage = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  private showUserError(message: string): void {
    this.userActionError = message;
    this.userActionMessage = '';

    if (this.userActionErrorTimeout) {
      clearTimeout(this.userActionErrorTimeout);
    }

    this.userActionErrorTimeout = setTimeout(() => {
      this.userActionError = '';
      this.cdr.detectChanges();
    }, 5000);
  }

  toggleUserStatus(account: any): void {
    if (account.role !== 'MEMBER' && account.role !== 'TEAM_ADMIN') {
      return;
    }

    const newStatus = !account.is_activate;
    const action = newStatus ? 'activate' : 'deactivate';

    this.updatingStatusUserId = account.id;
    this.userActionMessage = '';
    this.userActionError = '';

    this.dailyWorkService.updateUserStatus(account.id, newStatus).subscribe({
      next: () => {
        this.updatingStatusUserId = null;
        this.showUserSuccess(`${account.name} ${action}d successfully.`);

        // Refresh users and update the displayed counts
        this.loadUsers();
      },
      error: (error: any) => {
        this.updatingStatusUserId = null;
        this.showUserError(error?.error?.detail || `Failed to ${action} ${account.name}.`);
        this.cdr.detectChanges();
      },
    });
  }

  // Load historical edit requests across all teams.

  loadHistoricalEditRequests(): void {
    if (this.historicalRequestsLoading) {
      return;
    }

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
          this.historicalEditRequests = Array.isArray(response)
            ? response
            : (response.requests ?? response.edit_requests ?? []);

          this.requestsPage = 1;
        },
        error: (error: any) => {
          console.error('Historical edit requests loading failed:', error);

          this.historicalRequestsError =
            error?.error?.detail || 'Unable to load historical edit requests.';
        },
      });
  }

  // Approve or reject a pending historical edit request.
  reviewHistoricalRequest(request: any, status: 'APPROVED' | 'REJECTED'): void {
    if (request.status !== 'PENDING') {
      return;
    }

    const comment = (this.reviewComments[request.request_id] ?? '').trim();

    if (status === 'REJECTED' && !comment) {
      this.historicalRequestError = 'Please enter a review comment before rejecting the request.';
      this.historicalRequestMessage = '';
      return;
    }

    this.reviewingRequestId = request.request_id;
    this.historicalRequestError = '';
    this.historicalRequestMessage = '';

    this.dailyWorkService.reviewHistoricalEdit(request.request_id, status, comment).subscribe({
      next: () => {
        this.reviewingRequestId = null;

        this.historicalRequestMessage = `Request #${request.request_id} ${status.toLowerCase()} successfully.`;

        this.historicalRequestError = '';

        this.loadHistoricalEditRequests();
        this.loadHistoricalWorkAudit();
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        this.reviewingRequestId = null;

        this.historicalRequestError =
          error?.error?.detail || `Unable to ${status.toLowerCase()} this request.`;

        this.historicalRequestMessage = '';
        this.cdr.detectChanges();
      },
    });
  }

  // Load audit records for historical work changes.

  loadHistoricalWorkAudit(): void {
    if (this.historicalAuditLoading) {
      return;
    }

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
          this.historicalAuditRecords = response.audit_logs ?? [];
          this.auditPage = 1;
        },
        error: (error: any) => {
          console.error('Historical work audit loading failed:', error);

          this.historicalAuditError =
            error?.error?.detail || 'Unable to load historical work audit records.';
        },
      });
  }
}
