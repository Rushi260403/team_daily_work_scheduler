import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {

  email: string = '';
  password: string = '';

  errorMessage: string = '';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  login(): void {

    this.errorMessage = '';

    this.authService.login(
      this.email,
      this.password
    ).subscribe({

      next: (response) => {

        console.log('Login successful');
        console.log(response);

        if (response.access_token) {

          this.authService.saveToken(
            response.access_token
          );

          console.log('JWT token saved');

          const role = this.authService.getUserRole();

          console.log('User role:', role);

          if (role === 'MEMBER') {

            this.router.navigate(['/member-dashboard']);

          } else if (role === 'TEAM_ADMIN') {

            this.router.navigate(['/team-admin-dashboard']);

          } else if (role === 'SUPER_ADMIN') {

            this.router.navigate(['/super-admin-dashboard']);

          } else {

            this.errorMessage = 'Unknown user role';

          }

        }

      },

      error: (error) => {

        console.log('Login failed');
        console.log(error);

        this.errorMessage = 'Invalid email or password';

      }

    });

  }
}