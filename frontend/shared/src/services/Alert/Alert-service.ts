import {Subject, scan} from 'rxjs';
import {AlertColor} from '@mui/material';
import {uniqueNumber} from '../../utils/helpers';

export type TranslationObject = {
    key: string;
    ns: string;
    [key: string]: string | number; // Interpolation, replace tag in key
};

export type AlertType = {
    id?: number;
    severity?: AlertColor;
    highlight?: boolean;
    duration?: number;
    disabled?: boolean;
    removed?: boolean;
    sticky?: boolean;
    title?: TranslationObject;
    titlePlain?: string;
    body?: TranslationObject;
    bodyPlain?: string;
    bodyStrong?: TranslationObject;
    bodyStrongPlain?: string;
};

export type AlertTable = {[key: number]: AlertType};

const alertSubject$ = new Subject<AlertType[]>();

const AlertService = {
    showAlert$: alertSubject$.pipe(
        scan((acc, curr) => {
            const newAlert = curr[0];
            return newAlert.removed
                ? acc.filter((itm) => itm.id !== newAlert.id)
                : [...acc, newAlert];
        }),
    ),

    clearAlert(alert?: AlertType) {
        alertSubject$.next([{...alert, removed: true}]);
    },

    showAlert(alert: AlertType) {
        const newAlert: AlertType = {
            ...alert,
            id: uniqueNumber(),
        };
        if (!alert.disabled) {
            alertSubject$.next([newAlert]);
        }
        if (!alert.sticky) {
            setTimeout(() => {
                this.clearAlert(newAlert);
            }, alert.duration || 60000);
        }
    },
};

export default AlertService;
