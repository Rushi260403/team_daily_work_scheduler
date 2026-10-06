import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const authGuard: CanActivateFn = (route) => {

  const authService = inject(AuthService);
  const router = inject(Router);

  // Check if user is logged in
  if (!authService.isLoggedIn()) {

    router.navigate(['/']);

    return false;
  }

  // Get allowed role from route
  const allowedRole = route.data['role'];

  // If no role is specified, allow logged-in user
  if (!allowedRole) {
    return true;
  }

  // Get logged-in user's role from JWT
  const userRole = authService.getUserRole();

  // Check role
  if (userRole === allowedRole) {
    return true;
  }

  // User is logged in but does not have permission
  router.navigate(['/']);

  return false;
};