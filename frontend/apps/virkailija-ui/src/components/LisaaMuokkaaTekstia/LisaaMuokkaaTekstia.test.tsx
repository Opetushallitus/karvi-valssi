import {act, render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {IconButton} from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import {KyselyType} from '@cscfi/shared/services/Data/Data-service';
import {kyselyData} from '@cscfi/shared/utils/mockData';
import LisaaMuokkaaTekstia from './LisaaMuokkaaTekstia';

describe('<LisaaMuokkaaTekstia /> add', () => {
    const setKyselyMock = jest.fn();
    const kyselyMock: KyselyType = kyselyData[0];
    test('it should mount', () => {
        const kysymysId = -1;
        render(
            <LisaaMuokkaaTekstia
                kysely={kyselyMock}
                setKysely={setKyselyMock}
                selectedKysymysId={kysymysId}
            >
                {(openDialog) => (
                    <IconButton
                        onClick={() => {
                            openDialog();
                        }}
                        aria-label="edit"
                        color="default"
                        className="icon-button"
                        size="small"
                        data-testid="add"
                    >
                        <BuildIcon />
                    </IconButton>
                )}
            </LisaaMuokkaaTekstia>,
        );

        const addBtn = screen.getByTestId(/add/i);
        expect(addBtn).toBeInTheDocument();

        act(() => {
            addBtn.click();
        });

        const headingText = screen.getByText(/lisaa-uusi-teksti/i);
        expect(headingText).toBeInTheDocument();

        const fieldTitles = screen.getAllByText(/valiotsikko/i);
        expect(fieldTitles).toHaveLength(2);
    });

    test('it should show existing text', () => {
        const kysymysId = 965;
        render(
            <LisaaMuokkaaTekstia
                kysely={kyselyMock}
                setKysely={setKyselyMock}
                selectedKysymysId={kysymysId}
            >
                {(openDialog) => (
                    <IconButton
                        onClick={() => {
                            openDialog();
                        }}
                        aria-label="edit"
                        color="default"
                        className="icon-button"
                        size="small"
                        data-testid="edit"
                    >
                        <BuildIcon />
                    </IconButton>
                )}
            </LisaaMuokkaaTekstia>,
        );

        const editBtn = screen.getByTestId(/edit/i);
        expect(editBtn).toBeInTheDocument();

        act(() => {
            editBtn.click();
        });

        const headingText = screen.getByText(/muokkaa-tekstia/i);
        expect(headingText).toBeInTheDocument();

        const fieldTitles = screen
            .getAllByText(/valiotsikko/i)
            .filter((element) => element instanceof HTMLLabelElement);
        expect(fieldTitles).toHaveLength(2);
    });
});
