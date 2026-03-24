import {describe, test, expect} from 'vitest';
import {addHttpError} from './Error-service';

describe('Error', () => {
    test('it should exist', () => {
        expect(addHttpError).toBeTruthy();
    });
});
