import { Routes } from '@angular/router';
import { MoviesTableComponent } from './movies/movies-table/movies-table.component';
import { MovieFormComponent } from './movies/movie-form/movie-form.component';

export const routes: Routes = [
    { path: 'movies', component: MoviesTableComponent },
    { path: 'movies/:key', component: MovieFormComponent },
];
