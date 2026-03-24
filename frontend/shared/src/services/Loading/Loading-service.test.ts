import {describe, test, expect} from 'vitest';
import Loading from './Loading-service';

describe('Loading', () => {
    test('it should exist', () => {
        expect(Loading.startLoading).toBeTruthy();
    });
});
