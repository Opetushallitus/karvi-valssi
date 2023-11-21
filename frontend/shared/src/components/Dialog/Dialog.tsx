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

interface DialogProps {
    title: string;
    children?: ReactElement<any, string | JSXElementConstructor<any>>;
    cancel?: () => void;
    confirm?: () => void;
    content?: ReactNode;
    confirmBtnText?: string;
    cancelBtnText?: string;
    disableConfirm?: boolean;
    showDialogBoolean?: boolean;
}

function DialogComponent({
    title,
    children = null,
    confirm,
    cancel = () => false,
    content,
    confirmBtnText,
    cancelBtnText,
    showDialogBoolean = false,
    disableConfirm,
}: DialogProps) {
    const {t} = useTranslation(['confirmation']);
    const [showDialog, setShowDialog] = useState(showDialogBoolean);

    const onDialogClose = () => {
        setShowDialog(false);
    };

    const onConfirm = () => {
        if (confirm) {
            confirm();
        }
        onDialogClose();
    };

    return (
        <>
            {children && cloneElement(children)}
            {showDialog && (
                <Dialog open maxWidth={false} fullWidth disableRestoreFocus>
                    <h1>{title}</h1>
                    <div className="button-container-top">
                        <IconButton
                            className="icon-button"
                            aria-label={t('sulje-dialogi', {ns: 'yleiset'})}
                            onClick={cancel}
                        >
                            <CloseIcon />
                        </IconButton>
                    </div>
                    <div>{content}</div>
                    <div className="button-container">
                        {confirm && (
                            <button className="secondary" type="button" onClick={cancel}>
                                {cancelBtnText || t('peruuta')}
                            </button>
                        )}
                        <button
                            type="button"
                            disabled={disableConfirm}
                            onClick={onConfirm}
                        >
                            {confirmBtnText || title}
                        </button>
                    </div>
                </Dialog>
            )}
        </>
    );
}

export default DialogComponent;
