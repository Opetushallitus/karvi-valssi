import {act, render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {kyselyData} from '@cscfi/shared/utils/mockData';
import {IconButton} from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import LisaaMuokkaaKysymys from './LisaaMuokkaaKysymys';

describe('<LisaaMuokkaaKysymys />', () => {
    const kyselyMock = kyselyData[0];
    const setKyselyMock = jest.fn();
    test('it should mount', () => {
        const kysymysId = -1;
        render(
            <LisaaMuokkaaKysymys
                kysely={kyselyMock}
                setKysely={setKyselyMock}
                selectedKysymysId={kysymysId}
            >
                {(openDialog) => (
                    <Button
                        className="small"
                        startIcon={<AddIcon />}
                        onClick={openDialog}
                        data-testid="edit-btn"
                    >
                        Lisää uusi väittämä
                    </Button>
                )}
            </LisaaMuokkaaKysymys>,
        );

        const editBtn = screen.getByTestId('edit-btn');
        expect(editBtn).toBeInTheDocument();

        act(() => {
            editBtn.click();
        });

        const headingText = screen.getByText(/lisaa-uusi-vaittama-otsikko/i);
        expect(headingText).toBeInTheDocument();
        const textType = screen.getByText(/teksti-label/i);
        expect(textType).toBeInTheDocument();
        const questionTypeText = screen.getByText(/vaittaman-tyyppi/i);
        expect(questionTypeText).toBeInTheDocument();
    });

    test('it should show existing question', () => {
        const kysymysId = 234;
        render(
            <LisaaMuokkaaKysymys
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
                        data-testid="add-btn"
                    >
                        <BuildIcon />
                    </IconButton>
                )}
            </LisaaMuokkaaKysymys>,
        );

        const addBtn = screen.getByTestId('add-btn');
        expect(addBtn).toBeInTheDocument();

        act(() => {
            addBtn.click();
        });

        const headingText = screen.getByText(/muokkaa-vaittamaa-otsikko/i);
        expect(headingText).toBeInTheDocument();
        const existingQuestion = screen.getByDisplayValue(/kysymys1/i);
        expect(existingQuestion).toBeInTheDocument();
        const questionTypeText = screen.queryByText(/vaittaman-tyyppi/i);
        expect(questionTypeText).not.toBeInTheDocument();
    });
});
