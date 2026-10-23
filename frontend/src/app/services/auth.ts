import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Router } from '@angular/router'

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private apiUrl = 'http://localhost:8000/users';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  login(email: string, password: string): Observable<any> {

    const loginData = {
      email: email,
      password: password
    };

    return this.http.post(
      `${this.apiUrl}/login`,
      loginData
    );
  }

  saveToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isLoggedIn(): boolean {
    return this.getToken() !== null;
  }

  getUserRole(): string | null {

    const token = this.getToken();

    if (!token) {
      return null;
    }

    try {

      const payload = JSON.parse(
        atob(token.split('.')[1])
      );

      return payload.role || null;

    } catch (error) {

      console.error('Invalid JWT token');

      return null;
    }
  }

  logout(): void {
    localStorage.removeItem('access_token');
    this.router.navigate(['/']);
  }
}