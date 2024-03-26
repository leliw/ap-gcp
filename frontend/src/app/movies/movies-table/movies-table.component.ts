import { AfterViewInit, Component, ViewChild } from '@angular/core';
import { MatTableModule, MatTable } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MoviesTableDataSource } from './movies-table-datasource';
import { Movie, MoviesService } from '../movies.service';
import { MatFormField } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { RouterModule } from '@angular/router';



@Component({
    selector: 'app-movies-table',
    templateUrl: './movies-table.component.html',
    styleUrl: './movies-table.component.css',
    standalone: true,
    imports: [MatTableModule, MatPaginatorModule, MatSortModule, 
        MatFormField, MatInputModule, MatIconModule, MatButtonModule, RouterModule ]
})
export class MoviesTableComponent implements AfterViewInit {
    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;
    @ViewChild(MatTable) table!: MatTable<Movie>;
    dataSource!: MoviesTableDataSource;
    service: MoviesService;

    constructor(service: MoviesService) {
        this.service = service;
        this.dataSource = new MoviesTableDataSource(service);
    }
    
    displayedColumns = ['title', 'year', 'studio', 'director', 'actions'];

    ngAfterViewInit(): void {
        this.dataSource.sort = this.sort;
        this.dataSource.paginator = this.paginator;
        this.table.dataSource = this.dataSource;
    }

    applyFilter(event: Event) {
        const filterValue = (event.target as HTMLInputElement).value;
        this.dataSource.filter = filterValue.trim().toLowerCase();
        this.dataSource.filterChange.emit(filterValue);
        if (this.dataSource.paginator) {
            this.dataSource.paginator.firstPage();
        }
    }

    delete(movie: Movie) {
        this.service.delete(movie.title + "_" + movie.year).subscribe(() => {
            this.dataSource.data = this.dataSource.data.filter(m => m !== movie);
            this.dataSource.filterChange.emit("");
        });
    }

}
