import {render, screen} from '@testing-library/react';
import '@testing-library/jest-dom';
import {act} from 'react-dom/test-utils';
import {AlertColor} from '@mui/material';
import AlertService, {
    AlertType,
    TranslationObject,
} from '../../services/Alert/Alert-service';
import Alert from './Alert';

describe('<Alert />', () => {
    test('it should not fire alert', () => {
        // Alert should not be visible by default
        expect(screen.queryByTestId('Alert')).toBeNull();
    });

    test('it should fire alert and then clear it', () => {
        // Once launched, the alert is visible for 5 seconds (by default)
        // Check it becomes visible, and then clears after 5s.
        const title = {key: 'Alert Title'} as TranslationObject;
        const bodyStrong = {key: 'Body 1'} as TranslationObject;
        const body = {key: 'Body 2'} as TranslationObject;
        const severity: AlertColor = 'error';
        const duration = 5000;
        const newAlert: AlertType = {title, body, bodyStrong, severity, duration};
        jest.useFakeTimers();
        act(() => {
            render(<Alert />);
        });
        act(() => {
            AlertService.showAlert(newAlert);
        });
        act(() => {
            jest.advanceTimersByTime(1500);
        });
        expect(screen.getByTestId('Alert')).toBeInTheDocument();
        expect(screen.getByTestId('Alert')).toHaveTextContent(body.key);
        expect(screen.queryByText(title.key)).toBeInTheDocument();
        expect(screen.getByText(bodyStrong.key)).toBeInTheDocument();

        /*
        // autoclose disabled
        act(() => {
            jest.advanceTimersByTime(4000);
        });
        expect(screen.queryByTestId('Alert')).toBeNull();
        expect(screen.queryByText(title.key)).not.toBeInTheDocument();
        */
    });
});
