import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class DailyWorkService {
  private apiUrl = 'http://localhost:8000/daily-work';

  constructor(private http: HttpClient) {}

  getDashboard(): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.get(`${this.apiUrl}/dashboard`, { headers });
  }

  submitMorningWork(
    workDate: string,
    officeInTime: string,
    workingPoints: string,
  ): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    const data = {
      work_date: workDate,
      office_in_time: officeInTime,
      working_points: workingPoints,
    };

    return this.http.post(`${this.apiUrl}/morning`, data, { headers });
  }

  submitEveningWork(
    workDate: string,
    officeOutTime: string,
    pointsCompleted: string,
    pendingPoints: string,
  ): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    const data = {
      office_out_time: officeOutTime,
      points_completed: pointsCompleted,
      pending_points: pendingPoints,
    };

    return this.http.put(`${this.apiUrl}/evening/${workDate}`, data, { headers });
  }

  // 1. Submit a historical edit request
  requestHistoricalEdit(dailyWorkId: number, reason: string): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.post(
      `${this.apiUrl}/historical-edit-request`,
      {
        daily_work_id: dailyWorkId,
        request_reason: reason,
      },
      { headers },
    );
  }

  getHistoricalEditRequests(): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.get(`${this.apiUrl}/historical-edit-requests`, { headers });
  }

  // 2. Approve or reject a historical edit request
  reviewHistoricalEdit(
    requestId: number,
    status: 'APPROVED' | 'REJECTED',
    reviewComment: string,
  ): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.put(
      `${this.apiUrl}/historical-edit-request/${requestId}/review`,
      {
        status: status,
        review_comment: reviewComment,
      },
      { headers },
    );
  }

  // 3. Edit approved historical work
  editHistoricalWork(
    dailyWorkId: number,
    changes: {
      office_in_time?: string;
      working_points?: string;
      office_out_time?: string;
      points_completed?: string;
      pending_points?: string;
    },
  ): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.put(`${this.apiUrl}/historical-work/${dailyWorkId}/edit`, changes, {
      headers,
    });
  }

  // 4. Get historical edit audit logs
  getHistoricalWorkAudit(): Observable<any> {
    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    return this.http.get(`${this.apiUrl}/historical-work-audit`, { headers });
  }

  getMyWorkHistory(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>(`${this.apiUrl}/my`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getTeamMembers(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>('http://localhost:8000/users/team-members', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getTeamWorkHistory(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>(`${this.apiUrl}/team`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getAllWorkHistory(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>(`${this.apiUrl}/admin`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getAdminOverallSummary(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>(`${this.apiUrl}/admin/summary`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getAllUsers(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>('http://localhost:8000/users/', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  getAllTeams(): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.get<any>('http://localhost:8000/teams/', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  updateUserTeam(userId: number, teamId: number): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.put<any>(
      `http://localhost:8000/users/${userId}/team`,
      { team_id: teamId },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
  }

  createTeam(team: {
    team_name: string;
    academic_year: string;
    description: string;
  }): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.post<any>('http://localhost:8000/teams/', team, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }

  updateTeam(
    teamId: number,
    team: {
      team_name: string;
      academic_year: string;
      description: string;
      is_activate: boolean;
    },
  ): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.put<any>(`http://localhost:8000/teams/${teamId}`, team, {
      headers: { Authorization: `Bearer ${token}` },
    });
  }

  updateUserStatus(userId: number, isActivate: boolean): Observable<any> {
    const token = localStorage.getItem('access_token');

    return this.http.patch<any>(`http://localhost:8000/users/${userId}/activate`, null, {
      params: { is_activate: String(isActivate) },
      headers: { Authorization: `Bearer ${token}` },
    });
  }
}
