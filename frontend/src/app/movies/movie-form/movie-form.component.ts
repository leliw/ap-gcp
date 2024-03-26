import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Movie, MoviesService } from '../movies.service';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';

@Component({
    selector: 'app-movie-form',
    standalone: true,
    imports: [ CommonModule, MatCardModule, MatInputModule, ReactiveFormsModule, MatButtonModule ],
    templateUrl: './movie-form.component.html',
    styleUrl: './movie-form.component.css'
})
export class MovieFormComponent {

    key!: string;
    movie!: Movie;

    form = this.fb.nonNullable.group({
        title: ['', [Validators.required, Validators.minLength(5)]],
        year: [0, [Validators.required]],
        studio: ['', [Validators.required, Validators.minLength(5)]],
        director: ['', [Validators.required, Validators.minLength(5)]]
      });
    

    constructor(
        private fb: FormBuilder,
        private route: ActivatedRoute,
        private service: MoviesService
    ) {
        this.route.params.subscribe(params => {
            this.key = params['key'];
            if (this.key && this.key !== '__NEW__')
                this.service.get(this.key).subscribe(movie => {
                    this.movie = movie;
                    this.form.setValue(movie);
                });
          });
    }

    onSubmit() {
        if (this.form.invalid) return;
        const movie = this.form.getRawValue() as Movie;
        if (this.key === '__NEW__') {
            this.service.post(movie).subscribe(() => {
                this.form.reset();
            });
        } else {
            this.service.put(this.key, movie).subscribe(() => {
                this.form.reset();
            });
        }
    }
    
}
