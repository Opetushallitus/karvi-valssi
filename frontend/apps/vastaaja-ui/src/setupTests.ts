// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/vitest';
import {addI18nResources, initI18n} from '@cscfi/shared/test-utils';
import {vi, beforeAll, afterEach} from 'vitest';
import {of} from 'rxjs';
import {matrixScales} from '@cscfi/shared/utils/mockData';

const INITIAL_TRANSLATION = {};

beforeAll(() => {
    vi.mock('@cscfi/shared/services/http/http-service', () => ({
        arvoHttp: {
            get: () => of(),
            getWithCache: () => of(),
            post: () => of(),
        },
        raportointipalveluHttp: {
            getWithCache: () => of(),
        },
        vastauspalveluHttp: {
            get: () => of(),
            getWithCache: () => of(),
        },
        commonHttp: {
            getWithCache: () => of(),
        },
    }));
    vi.mock(
        '@cscfi/shared/services/Vastauspalvelu-api/Vastauspalvelu-api-service',
        async (importOriginal) => ({
            ...((await importOriginal()) as object),
            vastauspalveluGetMatrixScales$: () => of(matrixScales),
            vastauspalveluGetTempAnswers$: () => of([]),
            vastauspalveluGetKyselykerta$: () => of([]),
        }),
    );
    vi.mock('@cscfi/shared/services/Lokalisointi/Lokalisointi-service', () => ({
        default: () => of([]),
    }));

    initI18n(INITIAL_TRANSLATION);
});

afterEach(() => {
    // this would remove all existing translation and load initial one.
    addI18nResources(INITIAL_TRANSLATION);
});
