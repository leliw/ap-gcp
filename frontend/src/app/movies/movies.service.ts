import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


export interface Movie {
    title: string
    year: number
    studio: string
    director: string
}

@Injectable({
    providedIn: 'root'
})
export class MoviesService {

    constructor(private http: HttpClient) { }

    private endpoint = '/api/movies'

    getAll(): Observable<Movie[]> {
        return this.http.get<Movie[]>(this.endpoint);
    }

    post(movie: Movie): Observable<void> {
        return this.http.post<void>(this.endpoint, movie);
    }

    get(key: string): Observable<Movie> {
        const eKey = encodeURIComponent(key);
        return this.http.get<Movie>(`${this.endpoint}/${eKey}`);
    }

    put(key: string, movie: Movie): Observable<void> {
        const eKey = encodeURIComponent(key);
        return this.http.put<void>(`${this.endpoint}/${eKey}`, movie);
    }

    delete(key: string): Observable<void> {
        const eKey = encodeURIComponent(key);
        return this.http.delete<void>(`${this.endpoint}/${eKey}`);
    }

}
