import { SocialAuthService, SocialUser } from '@abacritt/angularx-social-login';
import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class AuthService {

    user: SocialUser | null = null;
    loggedIn: boolean = false;

    constructor(private socialAuthService: SocialAuthService) {
        this.socialAuthService.authState.subscribe((user) => {
            this.user = user;
            this.loggedIn = (user != null);
        });
    }

    public signOut(): void {
        this.socialAuthService.signOut();
        this.user = null;
        this.loggedIn = false;
    }

    public getToken(): string {
        return this.user?.idToken ?? '';
    }
    
}