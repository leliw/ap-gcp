import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    if (req.url.endsWith('/api/config')) {
        return next(req);
    } else {
        const authService = inject(AuthService);
        const authToken = authService.getToken();

        // Clone the request and add the authorization header
        const authReq = req.clone({
            setHeaders: {
                Authorization: `Bearer ${authToken}`
            }
        });
        return next(authReq);
    }
};