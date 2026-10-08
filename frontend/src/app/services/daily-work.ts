import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DailyWorkService {

  private apiUrl = 'http://localhost:8000/daily-work';

  constructor(private http: HttpClient) {}

  getDashboard(): Observable<any> {

    const token = localStorage.getItem('access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    return this.http.get(
      `${this.apiUrl}/dashboard`,
      { headers }
    );
  }
}