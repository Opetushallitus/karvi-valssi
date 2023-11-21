import {Subject, shareReplay} from 'rxjs';
import {debounceTime, distinctUntilChanged, map, scan} from 'rxjs/operators';

const isLoading$ = new Subject<number>();

const LoadingService = {
    isLoading$: isLoading$.pipe(
        scan((acc, current) => acc + current, 0),
        // tap((currentlyLoading) => console.log(`currentlyLoading ${currentlyLoading}`)),
        map((currentlyLoading) => currentlyLoading > 0),
        distinctUntilChanged(),
        debounceTime(100),
        shareReplay(1),
    ),
    startLoading() {
        isLoading$.next(1);
    },
    endLoading() {
        isLoading$.next(-1);
    },
};

export default LoadingService;
