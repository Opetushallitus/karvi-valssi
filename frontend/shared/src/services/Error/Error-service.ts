import {AlertColor} from '@mui/material';
import {AjaxError} from 'rxjs/ajax';
import AlertService, {AlertTable, AlertType} from '../Alert/Alert-service';

const createAlertType = (status) =>
    ({
        title: {key: `${status}-general-title`, ns: 'alert'},
        body: {key: `${status}-general-body`, ns: 'alert'},
    }) as AlertType;

const errorsByStatus = {
    401: createAlertType(401),
    403: createAlertType(403),
    400: createAlertType(400),
    404: createAlertType(404),
    500: createAlertType(500),
} as AlertTable;

const defaultError = {
    title: {key: 'general-title', ns: 'alert'},
    body: {key: 'general-body', ns: 'alert'},
} as AlertType;

export const addHttpError = ({status, message}: AjaxError, alertTable: AlertTable) => {
    const severity: AlertColor = 'error';
    const statusError = alertTable?.[status] || errorsByStatus[status];
    const alert: AlertType = statusError || defaultError;
    console.error(`Error status ${status}:`, message);
    AlertService.showAlert({severity, ...alert});
};

export default addHttpError;
