import {createTheme} from '@mui/material/styles';

const theme = createTheme({
    components: {
        MuiDialog: {
            defaultProps: {
                classes: {
                    // Forces Dialog, and it's subcomponents to conform with '.app' in index.css
                    root: 'app',
                },
            },
            styleOverrides: {
                root: {
                    // Some CSS here
                },
            },
        },
        MuiTableCell: {
            styleOverrides: {
                head: {
                    fontWeight: 'bold',
                },
                root: {
                    fontFamily: [
                        'Arial',
                        'Roboto',
                        'Oxygen',
                        'Helvetica Neue',
                        'sans-serif',
                    ],
                    borderBottom: 'none',
                    textAlign: 'center',
                    padding: '0.2rem 0.5rem',
                },
            },
        },
        MuiSvgIcon: {
            variants: [
                {
                    props: {fontVariant: 'externalLaunch'},
                    style: {
                        blockSize: 16,
                        marginLeft: '0.5rem',
                        verticalAlign: 'top',
                    },
                },
            ],
        },
        MuiAlert: {
            styleOverrides: {
                root: {
                    '& .MuiAlert-icon': {
                        alignItems: 'center',
                    },
                    '& .MuiAlert-message': {
                        margin: 'auto 0',
                    },
                    '& .MuiTypography-root': {
                        margin: 0,
                    },
                },
                filledWarning: {
                    backgroundColor: '#D64C1D',
                    color: 'white',
                    '& .MuiAlert-icon': {
                        color: 'white',
                    },
                    '& .MuiSvgIcon-root': {
                        // close btn
                        color: 'white',
                    },
                },
            },
        },
    },
});

export default theme;
