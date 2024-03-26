import { DataSource } from '@angular/cdk/collections';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { map } from 'rxjs/operators';
import { Observable, merge } from 'rxjs';
import { Movie, MoviesService } from '../movies.service';
import { EventEmitter } from '@angular/core';

export class MoviesTableDataSource extends DataSource<Movie> {
    data: Movie[] = [];
    paginator: MatPaginator | undefined;
    sort: MatSort | undefined;
    filter: string = "";
    filterChange = new EventEmitter<string>();

    constructor(private service: MoviesService) {
        super();
    }

    connect(): Observable<Movie[]> {
        if (this.paginator && this.sort) {
            return merge(this.service.getAll().pipe(map(data => this.data = data)),
                this.paginator.page, this.sort.sortChange, this.filterChange)
                .pipe(map(() => {
                    return this.getPagedData(this.getSortedData(this.getFilteredData([...this.data])));
                }));
        } else {
            throw Error('Please set the paginator and sort on the data source before connecting.');
        }
    }

    disconnect(): void {
        // No-op
    }

    private getPagedData(data: Movie[]): Movie[] {
        if (this.paginator) {
            const startIndex = this.paginator.pageIndex * this.paginator.pageSize;
            return data.splice(startIndex, this.paginator.pageSize);
        } else {
            return data;
        }
    }

    private getSortedData(data: Movie[]): Movie[] {
        if (!this.sort?.active || this.sort?.direction === '') {
            return data;
        }

        return data.sort((a, b) => {
            const isAsc = this.sort?.direction === 'asc';
            switch (this.sort?.active) {
                case 'title': return compare(a.title, b.title, isAsc);
                case 'year': return compare(+a.year, +b.year, isAsc);
                case 'studio': return compare(a.studio, b.studio, isAsc);
                case 'director': return compare(a.director, b.director, isAsc);
                default: return 0;
            }
        });
    }

    private getFilteredData(data: Movie[]): Movie[] {
        if (this.filter)
            return data.filter(movie =>
                movie.title.toLowerCase().includes(this.filter) ||
                movie.year.toString().includes(this.filter) ||
                movie.studio.toLowerCase().includes(this.filter) ||
                movie.director.toLowerCase().includes(this.filter)
            );
        else
            return data;
    }
}

/** Simple sort comparator for example ID/Name columns (for client-side sorting). */
function compare(a: string | number, b: string | number, isAsc: boolean): number {
    return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
