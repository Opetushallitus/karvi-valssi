import {
    cloneElement,
    useState,
    useMemo,
    useCallback,
    ReactNode,
    ReactElement,
    DetailedReactHTMLElement,
} from 'react';
import {useTranslation} from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import {Dialog} from '@mui/material';

interface ConfirmationDialogProps {
    title: string;
    content?: ReactNode;
    children?: ReactElement;
    cancel?: () => void;
    cancelBtnText?: string;
    cancelBtnHidden?: boolean;
    confirm?: () => void;
    confirmBtnText?: string;
    confirmBtnDisabled?: boolean;
    confirmBtnWarning?: boolean;
    showDialogBoolean?: boolean;
}

function ConfirmationDialog({
    title,
    content,
    children = null,
    confirm,
    cancel = () => false,
    cancelBtnText,
    cancelBtnHidden = false,
    confirmBtnText,
    confirmBtnDisabled = false,
    confirmBtnWarning = false,
    showDialogBoolean = false,
}: ConfirmationDialogProps) {
    const {t} = useTranslation(['confirmation']);
    const [showDialog, setShowDialog] = useState(showDialogBoolean);

    const showCancelBtn = useMemo(
        () => !!confirm && !cancelBtnHidden,
        [confirm, cancelBtnHidden],
    );

    const onDialogShow = useCallback(() => {
        setShowDialog(true);
    }, []);

    const onDialogClose = useCallback(() => {
        setShowDialog(false);
    }, []);

    const onConfirm = useCallback(() => {
        if (confirm) {
            confirm();
        }
        onDialogClose();
    }, [confirm, onDialogClose]);

    const onCancel = useCallback(() => {
        onDialogClose();
        cancel();
    }, [cancel, onDialogClose]);

    return (
        <>
            {children &&
                cloneElement(
                    children as DetailedReactHTMLElement<
                        {onClick: () => void},
                        HTMLElement
                    >,
                    {onClick: onDialogShow},
                )}

            <Dialog open={showDialog} maxWidth={false} fullWidth disableRestoreFocus>
                <div className="button-container-top">
                    <IconButton
                        className="icon-button"
                        aria-label={`${t('sulje-dialogi', {
                            ns: 'yleiset',
                        })} -${t('painike')}`}
                        onClick={() => onDialogClose()}
                    >
                        <CloseIcon />
                    </IconButton>
                </div>
                <h1>{title}</h1>
                <div>{content}</div>
                <div className="button-container">
                    {showCancelBtn && (
                        <button
                            className="secondary"
                            type="button"
                            onClick={onCancel}
                            aria-label={`${cancelBtnText || t('peruuta')}-${t(
                                'painike',
                            )}`}
                        >
                            {cancelBtnText || t('peruuta')}
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={confirmBtnDisabled}
                        className={confirmBtnWarning ? 'warning' : null}
                        aria-label={`${confirmBtnText || title}-${t('painike')}`}
                    >
                        {confirmBtnText || title}
                    </button>
                </div>
            </Dialog>
        </>
    );
}

export default ConfirmationDialog;
