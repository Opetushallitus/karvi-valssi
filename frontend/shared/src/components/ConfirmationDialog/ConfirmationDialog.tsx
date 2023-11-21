import {
    cloneElement,
    useState,
    ReactNode,
    ReactElement,
    JSXElementConstructor,
} from 'react';
import {useTranslation} from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import {Dialog} from '@mui/material';

interface ConfirmationDialogProps {
    title: string;
    children?: ReactElement<any, string | JSXElementConstructor<any>>;
    cancel?: () => void;
    confirm?: () => void;
    content?: ReactNode;
    confirmBtnText?: string;
    confirmBtnDisabled?: boolean;
    confirmBtnWarning?: boolean;
    cancelBtnText?: string;
    showDialogBoolean?: boolean;
}

function ConfirmationDialog({
    title,
    children = null,
    confirm,
    cancel = () => false,
    content,
    confirmBtnText,
    confirmBtnDisabled = false,
    confirmBtnWarning = false,
    cancelBtnText,
    showDialogBoolean = false,
}: ConfirmationDialogProps) {
    const {t} = useTranslation(['confirmation']);
    const [showDialog, setShowDialog] = useState(showDialogBoolean);

    const onDialogShow = () => {
        setShowDialog(true);
    };

    const onDialogClose = () => {
        setShowDialog(false);
    };

    const onConfirm = () => {
        if (confirm) {
            confirm();
        }
        onDialogClose();
    };

    const onCancel = () => {
        onDialogClose();
        cancel();
    };

    return (
        <>
            {children && cloneElement(children, {onClick: onDialogShow})}
            {showDialog && (
                <Dialog open maxWidth={false} fullWidth disableRestoreFocus>
                    <h1>{title}</h1>
                    <div className="button-container-top">
                        <IconButton
                            className="icon-button"
                            aria-label={t('sulje-dialogi', {ns: 'yleiset'})}
                            onClick={() => onDialogClose()}
                        >
                            <CloseIcon />
                        </IconButton>
                    </div>
                    <div>{content}</div>
                    <div className="button-container">
                        {confirm && (
                            <button
                                className="secondary"
                                type="button"
                                onClick={onCancel}
                            >
                                {cancelBtnText || t('peruuta')}
                            </button>
                        )}
                        <button
                            type="button"
                            onClick={onConfirm}
                            disabled={confirmBtnDisabled}
                            className={confirmBtnWarning ? 'warning' : null}
                        >
                            {confirmBtnText || title}
                        </button>
                    </div>
                </Dialog>
            )}
        </>
    );
}

export default ConfirmationDialog;
