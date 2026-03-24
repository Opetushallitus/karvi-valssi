import {useEffect, useRef} from 'react';
import {Alert, AlertTitle, IconButton, Snackbar} from '@mui/material';
import {useTranslation} from 'react-i18next';
import {useObservableState} from 'observable-hooks';
import CloseIcon from '@mui/icons-material/Close';
import AlertService, {AlertType} from '../../services/Alert/Alert-service';
import styles from './Alert.module.css';

function AlertBox({
    foundAlerts,
    isSticky,
}: {
    foundAlerts: AlertType[];
    isSticky?: boolean;
}) {
    const focusRef = useRef<HTMLDivElement>(null);
    const {t} = useTranslation();
    useEffect(() => {
        if (focusRef?.current && foundAlerts.length > 0) {
            focusRef.current.focus();
        }
    }, [foundAlerts]);
    const alertItem = (alert: AlertType) => {
        const {
            id,
            severity,
            highlight,
            title,
            titlePlain,
            body,
            bodyPlain,
            bodyStrong,
            bodyStrongPlain,
        } = alert;
        const titleTxt = titlePlain || t(title?.key, title).toString();
        const bodyTxt = bodyPlain || (body ? t(body?.key, body) : null);
        const bodyStrongTxt =
            bodyStrongPlain || (bodyStrong ? t(bodyStrong.key, bodyStrong) : null);
        return (
            <Alert
                data-testid="Alert"
                role="dialog"
                aria-modal="true"
                key={id}
                severity={severity || 'success'}
                variant={highlight ? 'filled' : 'standard'}
                action={
                    <IconButton
                        className="icon-button icon-button-alert"
                        aria-label={t('sulje-huomautus', {ns: 'yleiset'})}
                        component="span"
                        onClick={() => AlertService.clearAlert(alert)}
                    >
                        <CloseIcon />
                    </IconButton>
                }
            >
                <AlertTitle ref={focusRef} tabIndex={0}>
                    {titleTxt}
                </AlertTitle>
                {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
                <span tabIndex={0}>
                    {bodyTxt}
                    {bodyStrongTxt && (
                        <>
                            <span> — </span>
                            <strong>{bodyStrongTxt}</strong>
                        </>
                    )}
                </span>
            </Alert>
        );
    };

    if (foundAlerts?.length > 0) {
        return isSticky ? (
            <div className={styles.sticky}>
                {alertItem(foundAlerts.find((first) => !!first))}
            </div>
        ) : (
            <Snackbar
                anchorOrigin={{vertical: 'top', horizontal: 'center'}}
                open={foundAlerts.length > 0}
            >
                <div className={styles.snackbarlist}>
                    {foundAlerts.map((fa) => alertItem(fa))}
                </div>
            </Snackbar>
        );
    }
    return null;
}

export function StickyAlert() {
    const [foundAlerts] = useObservableState(() => AlertService.showAlert$, []).filter(
        (alItem) => (alItem as AlertType).sticky || false,
    );
    return <AlertBox foundAlerts={foundAlerts as AlertType[]} isSticky />;
}

export default function SnackBarAlert() {
    const [foundAlerts] = useObservableState(() => AlertService.showAlert$, []).filter(
        (alItem) => !(alItem as AlertType).sticky || false,
    );
    return <AlertBox foundAlerts={foundAlerts as AlertType[]} />;
}
