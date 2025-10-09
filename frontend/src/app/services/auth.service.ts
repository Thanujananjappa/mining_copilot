import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { environment } from '../../environments/environment';

export interface User {
  user_id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

export interface AuthResponse {
  success: boolean;
  /** ✅ Supports both access_token and token field names */
  access_token?: string;
  token?: string;
  refresh_token?: string;
  user?: User;
  message?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser: Observable<User | null>;

  constructor(private http: HttpClient, private router: Router) {
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(
      storedUser ? JSON.parse(storedUser) : null
    );
    this.currentUser = this.currentUserSubject.asObservable();
  }

  /** ✅ Get the current user */
  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /** ✅ Check if authenticated */
  public isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  /** ✅ Register */
  register(username: string, email: string, password: string, fullName: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, {
      username,
      email,
      password,
      full_name: fullName
    }).pipe(
      catchError(err => {
        console.error('Registration error:', err);
        return throwError(() => err);
      })
    );
  }

  /** ✅ Login */
  login(username: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, {
      username,
      password
    }).pipe(
      tap(response => {
        // ✅ Accept both "token" and "access_token"
        const token = response.access_token || response.token;

        if (response.success && token && response.user) {
          localStorage.setItem('access_token', token);
          if (response.refresh_token) {
            localStorage.setItem('refresh_token', response.refresh_token);
          }
          localStorage.setItem('currentUser', JSON.stringify(response.user));
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(err => {
        console.error('Login error:', err);
        return throwError(() => err);
      })
    );
  }

  /** ✅ Logout */
  logout(): void {
    const token = this.getAccessToken();
    if (token) {
      const headers = new HttpHeaders({ 'Authorization': `Bearer ${token}` });
      this.http.post(`${this.apiUrl}/logout`, {}, { headers }).subscribe({
        next: () => console.log('Logged out successfully.'),
        error: (err) => console.warn('Logout API failed:', err)
      });
    }

    // Clear everything
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);

    // Redirect
    this.router.navigate(['/login']);
  }

  /** ✅ Get tokens */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /** ✅ Refresh token */
  refreshToken(): Observable<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return throwError(() => new Error('No refresh token found.'));

    const headers = new HttpHeaders({ 'Authorization': `Bearer ${refreshToken}` });

    return this.http.post<AuthResponse>(`${this.apiUrl}/refresh`, {}, { headers }).pipe(
      tap(response => {
        const newToken = response.access_token || response.token;
        if (response.success && newToken) {
          localStorage.setItem('access_token', newToken);
        }
      }),
      catchError(err => {
        console.error('Token refresh error:', err);
        this.logout();
        return throwError(() => err);
      })
    );
  }

  /** ✅ Fetch current user info */
  getCurrentUser(): Observable<AuthResponse> {
    const token = this.getAccessToken();
    if (!token) return throwError(() => new Error('No token found.'));

    const headers = new HttpHeaders({ 'Authorization': `Bearer ${token}` });

    return this.http.get<AuthResponse>(`${this.apiUrl}/me`, { headers }).pipe(
      tap(response => {
        if (response.success && response.user) {
          localStorage.setItem('currentUser', JSON.stringify(response.user));
          this.currentUserSubject.next(response.user);
        }
      }),
      catchError(err => {
        console.error('Get user error:', err);
        this.logout();
        return throwError(() => err);
      })
    );
  }

  /** ✅ Change password */
  changePassword(currentPassword: string, newPassword: string): Observable<AuthResponse> {
    const token = this.getAccessToken();
    if (!token) return throwError(() => new Error('Not authenticated.'));

    const headers = new HttpHeaders({ 'Authorization': `Bearer ${token}` });

    return this.http.post<AuthResponse>(`${this.apiUrl}/change-password`, {
      current_password: currentPassword,
      new_password: newPassword
    }, { headers }).pipe(
      catchError(err => {
        console.error('Change password error:', err);
        return throwError(() => err);
      })
    );
  }
}
