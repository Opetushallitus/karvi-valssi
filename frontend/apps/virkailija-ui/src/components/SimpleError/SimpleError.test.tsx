import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {addI18nResources} from '@cscfi/shared/test-utils';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import SimpleError from './SimpleError';

describe('<SimpleError />', () => {
    test('it should mount', () => {
        render(<SimpleError />);

        const simpleError = screen.getByTestId('SimpleError');

        expect(simpleError).toBeInTheDocument();
    });

    test('it should print unknown error text', () => {
        addI18nResources(
            {
                'error-tuntematon-text': 'Tuntematon virhe',
            },
            {ns: 'yleiset'},
        );
        render(<SimpleError />);

        const localisedErrorText = screen.getByText(/Tuntematon virhe/i);
        expect(localisedErrorText).toBeInTheDocument();
    });

    test('it should print error text without link', () => {
        addI18nResources(
            {
                'error-no-link-text': 'Virheviesti ilman linkkiä',
            },
            {ns: 'yleiset'},
        );
        render(
            <MemoryRouter initialEntries={['/error/no-link']}>
                <Routes>
                    <Route path="/error/:errorKey" element={<SimpleError />} />
                </Routes>
            </MemoryRouter>,
        );

        const localisedErrorText = screen.getByText(/Virheviesti ilman linkkiä/i);
        expect(localisedErrorText).toBeInTheDocument();
    });

    test('it should print error text with link', () => {
        addI18nResources(
            {
                'error-with-link-title': 'Virheviestin otsikko',
                'error-with-link-text': 'Virheviesti linkillä <1>linkki</1>',
                'error-with-link-link': 'http://www.google.fi/',
            },
            {ns: 'yleiset'},
        );
        render(
            <MemoryRouter initialEntries={['/error/with-link']}>
                <Routes>
                    <Route path="/error/:errorKey" element={<SimpleError />} />
                </Routes>
            </MemoryRouter>,
        );

        const localisedErrorText = screen.getByText((content, node) => {
            const nodeHasText = node?.textContent === 'Virheviesti linkillä linkki';
            const childLink = node?.children?.[0] as HTMLLinkElement;
            const childHasText = childLink?.textContent === 'linkki';
            const childHasHref = childLink?.href === 'http://www.google.fi/';
            return nodeHasText && childHasText && childHasHref;
        });
        expect(localisedErrorText).toBeInTheDocument();
        const localisedErrorTitle = screen.getByText(/Virheviestin otsikko/i);
        expect(localisedErrorTitle).toBeInTheDocument();
    });

    test('it should allow p-tags in translation', () => {
        addI18nResources(
            {
                'error-with-link-text':
                    '<p>Virheviesti linkillä.</p> <p>Toinen virke <1>linkki</1></p>',
                'error-with-link-link': 'http://www.google.fi/',
            },
            {ns: 'yleiset'},
        );
        render(
            <MemoryRouter initialEntries={['/error/with-link']}>
                <Routes>
                    <Route path="/error/:errorKey" element={<SimpleError />} />
                </Routes>
            </MemoryRouter>,
        );

        const localisedErrorFirstText = screen.getByText(/Virheviesti linkillä/i);
        expect(localisedErrorFirstText).toBeInTheDocument();

        const localisedErrorSecondText = screen.getByText((content, node) => {
            const nodeHasText = node?.textContent === 'Toinen virke linkki';
            const childLink = node?.children?.[0] as HTMLLinkElement;
            const childHasText = childLink?.textContent === 'linkki';
            const childHasHref = childLink?.href === 'http://www.google.fi/';
            return nodeHasText && childHasText && childHasHref;
        });
        expect(localisedErrorSecondText).toBeInTheDocument();
    });

    test('it should print error text with link without http prefix', () => {
        addI18nResources(
            {
                'error-with-link-text': 'Virheviesti linkillä <1>linkki</1>',
                'error-with-link-link': 'www.google.fi/',
            },
            {ns: 'yleiset'},
        );
        render(
            <MemoryRouter initialEntries={['/error/with-link']}>
                <Routes>
                    <Route path="/error/:errorKey" element={<SimpleError />} />
                </Routes>
            </MemoryRouter>,
        );

        const localisedErrorText = screen.getByText((content, node) => {
            const nodeHasText = node?.textContent === 'Virheviesti linkillä linkki';
            const childLink = node?.children?.[0] as HTMLLinkElement;
            const childHasText = childLink?.textContent === 'linkki';
            const childHasHref = childLink?.href === 'http://www.google.fi/';
            return nodeHasText && childHasText && childHasHref;
        });
        expect(localisedErrorText).toBeInTheDocument();
    });
});
