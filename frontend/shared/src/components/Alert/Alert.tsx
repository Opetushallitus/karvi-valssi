import {useEffect, useRef} from 'react';
import {Alert, AlertTitle, Grid, IconButton, Snackbar} from '@mui/material';
import {useTranslation} from 'react-i18next';
import {useObservable} from 'rxjs-hooks';
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
    const focusRef = useRef<HTMLElement>(null);
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
                {/* eslint-disable-next-line jsx-a11y/tabindex-no-positive */}
                <AlertTitle ref={focusRef} tabIndex={0}>
                    {titleTxt}
                </AlertTitle>
                {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex,jsx-a11y/tabindex-no-positive */}
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

    if (foundAlerts.length > 0) {
        return isSticky ? (
            <div className={styles.sticky}>
                {alertItem(foundAlerts.find((first) => !!first))}
            </div>
        ) : (
            <Snackbar
                anchorOrigin={{vertical: 'top', horizontal: 'center'}}
                open={foundAlerts.length > 0}
            >
                <Grid
                    container
                    sx={{
                        justifyContent: 'center',
                        flexDirection: 'column-reverse',
                        columns: 1,
                        gap: '1rem',
                    }}
                >
                    {foundAlerts.map((fa) => alertItem(fa))}
                </Grid>
            </Snackbar>
        );
    }
    return null;
}

export function StickyAlert() {
    const foundAlerts = useObservable(() => AlertService.showAlert$, []).filter(
        (alItem) => alItem.sticky,
    );
    return <AlertBox foundAlerts={foundAlerts} isSticky />;
}

export default function SnackBarAlert() {
    const foundAlerts = useObservable(() => AlertService.showAlert$, []).filter(
        (alItem) => !alItem.sticky,
    );
    return <AlertBox foundAlerts={foundAlerts} />;
}
